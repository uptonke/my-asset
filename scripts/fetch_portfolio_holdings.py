#!/usr/bin/env python3
"""Fetch and normalize ETF holdings for Portfolio X-Ray.

Sources are deliberately source-specific instead of relying on one paid aggregator:
- QQQ: Invesco official JSON endpoint
- IFRA: iShares official CSV
- GRID: First Trust official holdings page
- COPX: Global X official full-holdings CSV discovered from the fund page
- VNM: VanEck official XLSX
- SRVR: CompaniesMarketCap fallback because Pacer blocks GitHub-hosted runners

Each fund is fetched independently. A failed refresh does not overwrite an existing
snapshot. The summary records fresh/stale/failure state so downstream analysis can
make data-quality limits explicit.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from openpyxl import load_workbook


FUNDS = ("QQQ", "IFRA", "GRID", "COPX", "VNM", "SRVR")
DEFAULT_OUTPUT_DIR = Path("data/holdings/latest")
HTTP_TIMEOUT = 35
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150 Safari/537.36 "
        "my-asset-holdings/1.0"
    ),
    "Accept": "*/*",
}


class HoldingsError(RuntimeError):
    pass


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _number(value: Any) -> float | None:
    text = _clean(value)
    if not text or text in {"-", "--", "N/A", "NA"}:
        return None
    negative = text.startswith("(") and text.endswith(")")
    text = text.strip("()")
    text = text.replace("$", "").replace(",", "").replace("%", "")
    try:
        out = float(text)
        return -out if negative else out
    except ValueError:
        return None


def _weight_decimal(value: Any) -> float | None:
    """Parse a source weight expressed in percentage points (e.g. 8.46 -> .0846)."""
    n = _number(value)
    return None if n is None else n / 100.0


def _iso_date(value: Any) -> str | None:
    text = _clean(value)
    if not text:
        return None
    formats = (
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%b %d, %Y",
        "%B %d, %Y",
    )
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            pass
    return None


def _extract_date(text: str) -> str | None:
    patterns = (
        r"\b(\d{1,2}/\d{1,2}/\d{4})\b",
        r"\b([A-Z][a-z]{2,8} \d{1,2}, \d{4})\b",
        r"\b(\d{4}-\d{2}-\d{2})\b",
    )
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            parsed = _iso_date(m.group(1))
            if parsed:
                return parsed
    return None


def _id_fields(preferred_type: str, preferred_value: Any, ticker: str, exchange: str = "") -> tuple[str, str]:
    ident = _clean(preferred_value)
    if ident and ident not in {"-", "--", "N/A"}:
        return preferred_type, ident
    ticker = _clean(ticker)
    exchange = _clean(exchange)
    if exchange and ticker:
        return "EXCHANGE_TICKER", f"{exchange}:{ticker}"
    return "TICKER", ticker


def _asset_class(raw: Any, ticker: str = "", name: str = "") -> str:
    text = " ".join((_clean(raw), _clean(ticker), _clean(name))).lower()
    if any(x in text for x in ("cash", "currency", "us dollar", "new taiwan dollar", "euro ", "sterling", "renminbi", "won ")):
        return "cash"
    if any(x in text for x in ("future", "option", "swap", "derivative")):
        return "derivative"
    if any(x in text for x in ("bond", "fixed income", "treasury", "note")):
        return "fixed_income"
    return "equity"


def _holding(
    *,
    ticker: Any,
    name: Any,
    weight: float | None,
    id_type: str,
    identifier: Any,
    exchange: Any = "",
    country: Any = "",
    currency: Any = "",
    asset_class: Any = "equity",
    sector: Any = "",
    shares: Any = None,
) -> dict[str, Any] | None:
    if weight is None or not math.isfinite(weight):
        return None
    ticker_s = _clean(ticker)
    name_s = _clean(name)
    exchange_s = _clean(exchange)
    id_type_s, id_s = _id_fields(id_type, identifier, ticker_s, exchange_s)
    if not (ticker_s or name_s or id_s):
        return None
    return {
        "id_type": id_type_s,
        "id": id_s,
        "ticker": ticker_s,
        "name": name_s,
        "exchange": exchange_s or None,
        "country": _clean(country) or None,
        "currency": _clean(currency) or None,
        "asset_class": _asset_class(asset_class, ticker_s, name_s),
        "sector": _clean(sector) or None,
        "weight": round(float(weight), 10),
        "shares": _number(shares),
    }


def _finalize(
    *,
    fund: str,
    as_of: str | None,
    source: str,
    source_quality: str,
    source_url: str,
    holdings: list[dict[str, Any]],
    reported_count: int | None = None,
    fallback_reason: str | None = None,
) -> dict[str, Any]:
    if not as_of:
        raise HoldingsError(f"{fund}: source date missing")
    holdings = [h for h in holdings if h]
    if not holdings:
        raise HoldingsError(f"{fund}: no holdings parsed")

    total_weight = sum(h["weight"] for h in holdings)
    equity_weight = sum(h["weight"] for h in holdings if h["asset_class"] == "equity")
    as_of_date = date.fromisoformat(as_of)
    stale_days = max(0, (datetime.now(timezone.utc).date() - as_of_date).days)

    # Sanity bounds catch HTML/CSV parser drift before a bad file replaces cache.
    if len(holdings) < 10:
        raise HoldingsError(f"{fund}: suspiciously low row count {len(holdings)}")
    if not 0.80 <= total_weight <= 1.20:
        raise HoldingsError(f"{fund}: parsed weight sum {total_weight:.4f} outside sanity range")

    return {
        "schema_version": 1,
        "fund": fund,
        "as_of": as_of,
        "fetched_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source": source,
        "source_quality": source_quality,
        "source_url": source_url,
        "lookthrough_mode": "EQUITY_LOOKTHROUGH",
        "coverage_pct": round(total_weight * 100.0, 4),
        "equity_coverage_pct": round(equity_weight * 100.0, 4),
        "stale_days": stale_days,
        "holdings_count": len(holdings),
        "reported_holdings_count": reported_count,
        "fallback_reason": fallback_reason,
        "holdings": holdings,
    }


def fetch_qqq(session: requests.Session) -> dict[str, Any]:
    url = (
        "https://dng-api.invesco.com/cache/v1/accounts/en_US/shareclasses/QQQ/"
        "holdings/fund?idType=ticker&interval=monthly&productType=ETF"
    )
    r = session.get(
        url,
        timeout=HTTP_TIMEOUT,
        headers={
            "User-Agent": "Mozilla/5.0 my-asset-holdings/1.0",
            "Accept": "application/json,text/plain,*/*",
            "Referer": "https://www.invesco.com/qqq-etf/en/about.html",
        },
    )
    r.raise_for_status()
    data = r.json()
    raw_rows = data.get("holdings") or []
    holdings: list[dict[str, Any]] = []
    for row in raw_rows:
        h = _holding(
            ticker=row.get("ticker"),
            name=row.get("issuerName"),
            weight=_weight_decimal(row.get("percentageOfTotalNetAssets")),
            id_type="CUSIP",
            identifier=row.get("cusip"),
            currency=row.get("currency") or row.get("localCurrencyName"),
            asset_class=row.get("securityTypeName"),
            shares=row.get("units"),
        )
        if h:
            holdings.append(h)
    as_of = _iso_date(data.get("effectiveBusinessDate")) or _iso_date(data.get("effectiveDate"))
    return _finalize(
        fund="QQQ",
        as_of=as_of,
        source="Invesco official DNG holdings API",
        source_quality="OFFICIAL_DAILY",
        source_url=url,
        holdings=holdings,
        reported_count=int(data.get("totalNumberOfHoldings")) if str(data.get("totalNumberOfHoldings", "")).isdigit() else None,
    )


def fetch_ifra(session: requests.Session) -> dict[str, Any]:
    url = "https://www.ishares.com/us/products/294315/ishares-u-s-infrastructure-etf/latest-holdings.csv"
    r = session.get(url, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    text = r.content.decode("utf-8-sig", errors="replace")
    lines = text.splitlines()
    try:
        header_idx = next(i for i, line in enumerate(lines) if line.startswith("Ticker,"))
    except StopIteration as exc:
        raise HoldingsError("IFRA: CSV header not found") from exc
    as_of = _extract_date(" ".join(lines[:header_idx]))
    rows = csv.DictReader(io.StringIO("\n".join(lines[header_idx:])))
    holdings: list[dict[str, Any]] = []
    for row in rows:
        ticker = row.get("Ticker", "")
        name = row.get("Name", "")
        weight = _weight_decimal(row.get("Weight (%)"))
        if weight is None:
            continue
        h = _holding(
            ticker=ticker,
            name=name,
            weight=weight,
            id_type="EXCHANGE_TICKER",
            identifier="",
            exchange=row.get("Exchange"),
            country=row.get("Location"),
            currency=row.get("Currency") or row.get("Market Currency"),
            asset_class=row.get("Asset Class"),
            sector=row.get("Sector"),
            shares=row.get("Quantity"),
        )
        if h:
            holdings.append(h)
    return _finalize(
        fund="IFRA",
        as_of=as_of,
        source="iShares official holdings CSV",
        source_quality="OFFICIAL_DAILY",
        source_url=url,
        holdings=holdings,
    )


def fetch_grid(session: requests.Session) -> dict[str, Any]:
    url = "https://www.ftportfolios.com/Retail/Etf/EtfHoldings.aspx?Ticker=GRID"
    r = session.get(url, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    page_text = soup.get_text(" ", strip=True)
    m = re.search(r"Holdings of the Fund as of\s+([0-9/]+)", page_text, re.I)
    as_of = _iso_date(m.group(1)) if m else None
    count_m = re.search(r"Total Number of Holdings \(excluding cash\):\s*(\d+)", page_text, re.I)
    reported_count = int(count_m.group(1)) if count_m else None

    holdings: list[dict[str, Any]] = []
    for tr in soup.find_all("tr"):
        # recursive=False prevents page-layout tables from swallowing the holdings table.
        cells = [_clean(c.get_text(" ", strip=True)) for c in tr.find_all(["td", "th"], recursive=False)]
        if len(cells) != 7:
            continue
        name, ticker, cusip, classification, shares, _market_value, weight_text = cells
        weight = _weight_decimal(weight_text)
        if weight is None or name.lower() == "security name":
            continue
        # Data rows have a security identifier/ticker plus a percent weighting.
        if not re.fullmatch(r"-?\d+(?:\.\d+)?%", weight_text.replace(" ", "")):
            continue
        h = _holding(
            ticker=ticker,
            name=name,
            weight=weight,
            id_type="CUSIP",
            identifier=cusip,
            asset_class="cash" if ticker.startswith("$") or classification.lower() == "other" else "equity",
            sector=classification,
            shares=shares,
        )
        if h:
            holdings.append(h)
    return _finalize(
        fund="GRID",
        as_of=as_of,
        source="First Trust official holdings page",
        source_quality="OFFICIAL_DAILY",
        source_url=url,
        holdings=holdings,
        reported_count=reported_count,
    )


def fetch_copx(session: requests.Session) -> dict[str, Any]:
    page_url = "https://www.globalxetfs.com/funds/COPX"
    p = session.get(page_url, timeout=HTTP_TIMEOUT)
    p.raise_for_status()
    soup = BeautifulSoup(p.text, "html.parser")
    csv_links: list[str] = []
    for a in soup.find_all("a", href=True):
        href = str(a["href"])
        if "full-holdings" in href.lower() and href.lower().endswith(".csv"):
            csv_links.append(urljoin(page_url, href))
    if not csv_links:
        csv_links = re.findall(
            r'https?://[^"\']*copx[^"\']*full-holdings[^"\']*\.csv',
            p.text,
            flags=re.I,
        )
    if not csv_links:
        raise HoldingsError("COPX: official full-holdings CSV link not found")
    csv_url = csv_links[0]
    r = session.get(csv_url, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    text = r.content.decode("utf-8-sig", errors="replace")
    lines = text.splitlines()
    try:
        header_idx = next(i for i, line in enumerate(lines) if line.startswith("% of Net Assets,Ticker,Name,"))
    except StopIteration as exc:
        raise HoldingsError("COPX: CSV header not found") from exc
    as_of = _extract_date(" ".join(lines[:header_idx])) or _extract_date(csv_url)
    rows = csv.DictReader(io.StringIO("\n".join(lines[header_idx:])))
    holdings: list[dict[str, Any]] = []
    for row in rows:
        h = _holding(
            ticker=row.get("Ticker"),
            name=row.get("Name"),
            weight=_weight_decimal(row.get("% of Net Assets")),
            id_type="SEDOL",
            identifier=row.get("SEDOL"),
            asset_class="equity",
            shares=row.get("Shares Held"),
        )
        if h:
            holdings.append(h)
    return _finalize(
        fund="COPX",
        as_of=as_of,
        source="Global X official full holdings CSV",
        source_quality="OFFICIAL_DAILY",
        source_url=csv_url,
        holdings=holdings,
    )


def fetch_vnm(session: requests.Session) -> dict[str, Any]:
    url = "https://www.vaneck.com/us/en/investments/vietnam-etf-vnm/downloads/holdings/"
    r = session.get(url, timeout=HTTP_TIMEOUT, allow_redirects=True)
    r.raise_for_status()
    wb = load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = [list(row) for row in ws.iter_rows(values_only=True)]
    as_of = _extract_date(" ".join(_clean(x) for row in rows[:8] for x in row if x is not None))
    if not as_of:
        as_of = _extract_date(wb.sheetnames[0].replace("_", "/"))

    header_idx = None
    headers: list[str] = []
    for idx, row in enumerate(rows):
        normalized = [_clean(x) for x in row]
        if "Ticker" in normalized and any("Net Assets" in x for x in normalized):
            header_idx = idx
            headers = normalized
            break
    if header_idx is None:
        raise HoldingsError("VNM: holdings header row not found")
    index = {name: i for i, name in enumerate(headers) if name}

    def cell(row: list[Any], key: str) -> Any:
        i = index.get(key)
        return row[i] if i is not None and i < len(row) else None

    weight_header = next((h for h in headers if "Net Assets" in h), "% of Net Assets")
    holdings: list[dict[str, Any]] = []
    for row in rows[header_idx + 1 :]:
        ticker = cell(row, "Ticker")
        name = cell(row, "Holding Name")
        weight = _weight_decimal(cell(row, weight_header))
        if weight is None:
            continue
        h = _holding(
            ticker=ticker,
            name=name,
            weight=weight,
            id_type="FIGI",
            identifier=cell(row, "Identifier (FIGI)"),
            asset_class=cell(row, "Asset Class"),
            shares=cell(row, "Shares"),
        )
        if h:
            holdings.append(h)
    return _finalize(
        fund="VNM",
        as_of=as_of,
        source="VanEck official holdings XLSX",
        source_quality="OFFICIAL_DAILY",
        source_url=url,
        holdings=holdings,
    )


def fetch_srvr(session: requests.Session) -> dict[str, Any]:
    # Pacer's official site currently returns Cloudflare 403 from GitHub-hosted runners.
    # Keep this fallback explicitly lower-quality rather than pretending it is issuer data.
    url = "https://companiesmarketcap.com/pacer-benchmark-data-infrastructure-real-estate-sctr-etf/holdings/"
    r = session.get(url, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    page_text = soup.get_text(" ", strip=True)
    m = re.search(r"Etf holdings as of ([A-Za-z]+ \d{1,2}, \d{4})", page_text, re.I)
    as_of = _iso_date(m.group(1)) if m else None
    count_m = re.search(r"Number of holdings:\s*(\d+)", page_text, re.I)
    reported_count = int(count_m.group(1)) if count_m else None

    holdings: list[dict[str, Any]] = []
    for tr in soup.find_all("tr"):
        cells = [_clean(c.get_text(" ", strip=True)) for c in tr.find_all(["td", "th"], recursive=False)]
        if len(cells) < 4:
            continue
        weight_text, name, ticker, shares = cells[:4]
        if not re.fullmatch(r"-?\d+(?:\.\d+)?%", weight_text.replace(" ", "")):
            continue
        h = _holding(
            ticker=ticker,
            name=name,
            weight=_weight_decimal(weight_text),
            id_type="TICKER",
            identifier=ticker,
            asset_class="equity",
            shares=shares,
        )
        if h:
            holdings.append(h)
    return _finalize(
        fund="SRVR",
        as_of=as_of,
        source="CompaniesMarketCap holdings fallback",
        source_quality="THIRD_PARTY_FALLBACK",
        source_url=url,
        holdings=holdings,
        reported_count=reported_count,
        fallback_reason="Pacer official holdings page is blocked by Cloudflare on GitHub-hosted runners.",
    )


FETCHERS = {
    "QQQ": fetch_qqq,
    "IFRA": fetch_ifra,
    "GRID": fetch_grid,
    "COPX": fetch_copx,
    "VNM": fetch_vnm,
    "SRVR": fetch_srvr,
}


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def run(output_dir: Path, strict: bool = False, funds: tuple[str, ...] = FUNDS) -> int:
    session = _session()
    summary: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "funds": {},
    }
    hard_failures = 0

    for fund in funds:
        fetcher = FETCHERS[fund]
        path = output_dir / f"{fund}.json"
        try:
            payload = fetcher(session)
            _write_json(path, payload)
            summary["funds"][fund] = {
                "status": "FRESH",
                "as_of": payload["as_of"],
                "stale_days": payload["stale_days"],
                "source_quality": payload["source_quality"],
                "holdings_count": payload["holdings_count"],
                "coverage_pct": payload["coverage_pct"],
                "equity_coverage_pct": payload["equity_coverage_pct"],
            }
            print(
                f"✅ {fund}: {payload['holdings_count']} rows, "
                f"coverage={payload['coverage_pct']:.2f}%, as_of={payload['as_of']}, "
                f"source={payload['source_quality']}",
                flush=True,
            )
        except Exception as exc:
            cached = None
            if path.exists():
                try:
                    cached = json.loads(path.read_text(encoding="utf-8"))
                except Exception:
                    cached = None
            if cached:
                summary["funds"][fund] = {
                    "status": "STALE_CACHE",
                    "as_of": cached.get("as_of"),
                    "stale_days": cached.get("stale_days"),
                    "source_quality": cached.get("source_quality"),
                    "holdings_count": cached.get("holdings_count"),
                    "coverage_pct": cached.get("coverage_pct"),
                    "equity_coverage_pct": cached.get("equity_coverage_pct"),
                    "refresh_error": f"{type(exc).__name__}: {exc}",
                }
                print(f"⚠️ {fund}: refresh failed; retained cached snapshot: {exc}", flush=True)
                if strict:
                    hard_failures += 1
            else:
                hard_failures += 1
                summary["funds"][fund] = {
                    "status": "FAILED_NO_CACHE",
                    "refresh_error": f"{type(exc).__name__}: {exc}",
                }
                print(f"❌ {fund}: no usable snapshot: {exc}", flush=True)

    statuses = [v.get("status") for v in summary["funds"].values()]
    summary["fresh_count"] = statuses.count("FRESH")
    summary["stale_cache_count"] = statuses.count("STALE_CACHE")
    summary["failed_count"] = statuses.count("FAILED_NO_CACHE")
    _write_json(output_dir / "summary.json", summary)

    if hard_failures:
        print(f"Holdings ingestion completed with {hard_failures} hard failure(s).", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--strict", action="store_true", help="Fail if any requested fresh fetch fails.")
    parser.add_argument("--fund", action="append", choices=FUNDS, help="Fetch only selected fund(s).")
    args = parser.parse_args()
    funds = tuple(args.fund) if args.fund else FUNDS
    return run(args.output_dir, strict=args.strict, funds=funds)


if __name__ == "__main__":
    raise SystemExit(main())
