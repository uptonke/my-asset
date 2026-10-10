from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from individual_stock_risk_policy import (  # noqa: E402
    classify_instrument,
    enforce_individual_stock_policy,
    load_policy,
)


class IndividualStockRiskPolicyTests(unittest.TestCase):
    def test_classifier_distinguishes_tw_and_us_funds_from_direct_stocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            holdings_dir = root / "data" / "holdings" / "latest"
            holdings_dir.mkdir(parents=True)
            (holdings_dir / "QQQ.json").write_text(
                json.dumps({"holdings": [{"ticker": "NVDA", "asset_class": "equity", "weight": 0.10}]}),
                encoding="utf-8",
            )
            self.assertEqual(
                classify_instrument({"ticker": "00981A", "asset_kind": "taiwan"}, root),
                "tw_etf",
            )
            self.assertEqual(
                classify_instrument({"ticker": "2382", "asset_kind": "taiwan"}, root),
                "tw_individual_stock",
            )
            self.assertEqual(
                classify_instrument({"ticker": "QQQ", "asset_kind": "us"}, root),
                "us_etf",
            )
            self.assertEqual(
                classify_instrument({"ticker": "AAPL", "asset_kind": "us"}, root),
                "us_individual_stock",
            )
            self.assertEqual(
                classify_instrument({"ticker": "BOXX", "asset_kind": "us"}, root),
                "us_cash_like",
            )

    def test_tw_and_us_direct_stock_caps_include_etf_lookthrough(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            holdings_dir = root / "data" / "holdings" / "latest"
            holdings_dir.mkdir(parents=True)
            (holdings_dir / "00981A.json").write_text(
                json.dumps({
                    "holdings": [
                        {"ticker": "2382", "asset_class": "equity", "country": "Taiwan", "weight": 0.12}
                    ]
                }),
                encoding="utf-8",
            )
            (holdings_dir / "QQQ.json").write_text(
                json.dumps({
                    "holdings": [
                        {"ticker": "NVDA", "asset_class": "equity", "country": "United States", "weight": 0.20}
                    ]
                }),
                encoding="utf-8",
            )

            rows = [
                {"ticker": "00981A", "asset_kind": "taiwan", "category": "台股"},
                {"ticker": "2382", "asset_kind": "taiwan", "category": "台股"},
                {"ticker": "2317", "asset_kind": "taiwan", "category": "台股"},
                {"ticker": "QQQ", "asset_kind": "us", "category": "美股"},
                {"ticker": "NVDA", "asset_kind": "us", "category": "美股"},
                {"ticker": "MSFT", "asset_kind": "us", "category": "美股"},
                {"ticker": "BOXX", "asset_kind": "us", "category": "美股"},
            ]
            guarded, diagnostics, _ = enforce_individual_stock_policy(
                root=root,
                weights={
                    "00981A": 0.10,
                    "2382": 0.18,
                    "2317": 0.12,
                    "QQQ": 0.20,
                    "NVDA": 0.18,
                    "MSFT": 0.12,
                    "BOXX": 0.10,
                },
                asset_rows=rows,
                investable=1.0,
                min_weight=0.02,
                global_max_weight=0.40,
                policy=load_policy({}),
            )

            self.assertAlmostEqual(sum(guarded.values()), 1.0, places=7)
            self.assertLessEqual(guarded.get("2382", 0.0), 0.08 + 1e-8)
            self.assertLessEqual(guarded.get("2317", 0.0), 0.08 + 1e-8)
            self.assertLessEqual(guarded.get("2382", 0.0) + guarded.get("2317", 0.0), 0.15 + 1e-8)
            self.assertLessEqual(guarded.get("NVDA", 0.0), 0.10 + 1e-8)
            self.assertLessEqual(guarded.get("MSFT", 0.0), 0.10 + 1e-8)
            self.assertLessEqual(guarded.get("NVDA", 0.0) + guarded.get("MSFT", 0.0), 0.25 + 1e-8)

            tw_diag = diagnostics["markets"]["taiwan"]
            us_diag = diagnostics["markets"]["us"]
            self.assertLessEqual(tw_diag["final_issuer_exposure_pct"]["2382"], 10.00001)
            self.assertLessEqual(us_diag["final_issuer_exposure_pct"]["NVDA"], 15.00001)

    def test_no_direct_stock_is_identity(self) -> None:
        weights = {"00981A": 0.20, "VOO": 0.50, "BOXX": 0.30}
        rows = [
            {"ticker": "00981A", "asset_kind": "taiwan", "category": "台股"},
            {"ticker": "VOO", "asset_kind": "us", "category": "美股"},
            {"ticker": "BOXX", "asset_kind": "us", "category": "美股"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            guarded, _, warnings = enforce_individual_stock_policy(
                root=Path(tmp),
                weights=weights,
                asset_rows=rows,
                investable=1.0,
                min_weight=0.02,
                global_max_weight=0.40,
                policy=load_policy({}),
            )
        self.assertEqual(guarded, weights)
        self.assertEqual(warnings, [])

    def test_policy_overrides_accept_ratio_or_percent(self) -> None:
        policy = load_policy({
            "delegated_draft_policy": {
                "us_individual_stock_max_weight_pct": 8,
                "us_individual_stock_sleeve_max_weight_pct": 0.20,
                "us_single_issuer_lookthrough_max_weight_pct": 12,
            }
        })
        self.assertAlmostEqual(policy["markets"]["us"]["individual_max_weight"], 0.08)
        self.assertAlmostEqual(policy["markets"]["us"]["individual_sleeve_max_weight"], 0.20)
        self.assertAlmostEqual(policy["markets"]["us"]["issuer_lookthrough_max_weight"], 0.12)


if __name__ == "__main__":
    unittest.main()
