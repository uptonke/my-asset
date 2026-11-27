import sys
import tempfile
import json
import unittest
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import fetch_portfolio_holdings as m

class HoldingsQualityTests(unittest.TestCase):
    def test_age_recomputed_and_policy(self):
        p={"as_of":"2026-07-31","stale_days":1,"source_quality":"OFFICIAL_MONTHLY","coverage_pct":99.9}
        r=m.snapshot_quality(p,date(2026,11,27))
        self.assertEqual(r["stale_days"],119)
        self.assertEqual(r["freshness"],"STALE")
        self.assertEqual(m.snapshot_quality({**p,"as_of":"2026-12-01"},date(2026,11,27))["freshness"],"UNKNOWN")
        self.assertEqual(m.snapshot_quality({**p,"coverage_pct":88},date(2026,11,27))["coverage_status"],"PARTIAL")

    def test_stale_response_and_regression(self):
        today=datetime.now(timezone.utc).date()
        old=(today-timedelta(days=120)).isoformat()
        payload={"as_of":old,"stale_days":1,"source_quality":"OFFICIAL_MONTHLY","holdings_count":500,
                 "coverage_pct":99.9,"equity_coverage_pct":99.9}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"latest"
            with patch.dict(m.FETCHERS,{"VOO":lambda s:payload}):
                self.assertEqual(m.run(root,funds=("VOO",)),0)
            summary=json.loads((root/"summary.json").read_text())["funds"]["VOO"]
            self.assertEqual(summary["status"],"STALE_SOURCE")
            self.assertEqual(summary["stale_days"],120)
            self.assertTrue((root.parent/"archive"/today.isoformat()/"VOO.json").exists())
            with patch.dict(m.FETCHERS,{"VOO":lambda s:{**payload,"as_of":(today-timedelta(days=121)).isoformat()}}):
                self.assertEqual(m.run(root,funds=("VOO",)),0)
            summary=json.loads((root/"summary.json").read_text())["funds"]["VOO"]
            self.assertEqual(summary["status"],"STALE_CACHE")
            self.assertEqual(summary["stale_days"],120)
            self.assertEqual(json.loads((root/"VOO.json").read_text())["as_of"],old)

class SourceRecoveryTests(unittest.TestCase):
    def test_ishares_market_weight_not_notional(self):
        from unittest.mock import Mock
        r=Mock()
        rows=[f'S{i},Sterling Infrastructure {i},Equity,10,20,NYSE,United States,USD' for i in range(10)]
        r.content=('Fund Holdings as of,"Nov 25, 2026"\nTicker,Name,Asset Class,Market Weight,Notional Weight,Exchange,Location,Currency\n'+'\n'.join(rows)).encode()
        session=Mock()
        session.get.return_value=r
        with patch.object(m,"datetime", wraps=m.datetime) as clock:
            clock.now.return_value=datetime(2026,11,27,tzinfo=timezone.utc)
            result=m._fetch_ishares_csv(session,fund="IFRA",product_id="294315",slug="fund")
        self.assertAlmostEqual(result["coverage_pct"],100)
        self.assertAlmostEqual(result["equity_coverage_pct"],100)

    def test_copx_dated_filename_and_partial_rejection(self):
        from unittest.mock import Mock
        r=Mock()
        r.content=('Net Assets (%),Ticker,Name,SEDOL,Shares Held\n'+'\n'.join(f'2.5%,S{i},Stock {i},ID{i},1' for i in range(40))).encode()
        url="https://assets.globalxetfs.com/funds/holdings/copx_full-holdings_20261125.csv"
        with patch.object(m,"datetime", wraps=m.datetime) as clock:
            clock.now.return_value=datetime(2026,11,27,tzinfo=timezone.utc)
            result=m._parse_copx_csv(r,url)
            self.assertEqual(result["as_of"],"2026-11-25")
            self.assertEqual(result["holdings_count"],40)
            r.content=b'Net Assets (%),Ticker,Name,SEDOL,Shares Held\n100%,X,Stock,ABC,1'
            with self.assertRaises(m.HoldingsError):
                m._parse_copx_csv(r,url)

    def test_vanguard_fallback(self):
        from unittest.mock import Mock
        with patch.object(m,"_fetch_vanguard_pages", side_effect=[m.HoldingsError("unavailable"),{"as_of":"2026-10-31"}]) as fetch:
            result=m.fetch_voo(Mock())
        self.assertEqual(result["as_of"],"2026-10-31")
        self.assertIn("/vmf/api/VOO/",fetch.call_args_list[0].args[2])
        self.assertIn("/profile/api/VOO/",fetch.call_args_list[1].args[2])

class VanguardDedupTests(unittest.TestCase):
    def row(self, ticker="ABC", isin="US1234567890", weight=40, shares=100, **kw):
        return {"ticker":ticker,"isin":isin,"longName":ticker+" Corp",
                "percentWeight":weight,"sharesHeld":shares,**kw}

    def test_distinct_positions_preserve_mass(self):
        rows=[self.row(),self.row(weight=20,shares=50),
              self.row("XYZ","N/A",40,100)]
        holdings,d=m._vanguard_normalize("VEA","2026-10-31",rows)
        self.assertEqual(len(holdings),2)
        self.assertAlmostEqual(holdings[0]["weight"],.6)
        self.assertEqual(holdings[0]["shares"],150)
        self.assertEqual(holdings[1]["id_type"],"VANGUARD_ROW")
        self.assertEqual(d["merged_position_rows"],1)
        self.assertEqual(d["unverified_identifier_rows"],1)
        self.assertAlmostEqual(d["raw_weight_pct"],d["normalized_weight_pct"])

    def test_placeholders_use_secondary_identifier(self):
        self.assertEqual(m._vanguard_identifier({"isin":"N/A","cusip":"123456789"}),("CUSIP","123456789"))
        self.assertIsNone(m._vanguard_identifier({"isin":"US0000000000","cusip":"000000000","sedol":"0000000"}))

    def test_conflict_and_economic_duplicate_rejected(self):
        with self.assertRaisesRegex(m.HoldingsError,"conflicting"):
            m._vanguard_normalize("VEA","2026-10-31",[self.row(),self.row("XYZ",weight=60)])
        with self.assertRaisesRegex(m.HoldingsError,"ambiguous repeated"):
            m._vanguard_normalize("VEA","2026-10-31",[self.row(),self.row(extra="different")])

    def test_repeated_raw_row_rejected(self):
        from unittest.mock import Mock
        session=Mock()
        r=Mock()
        r.json.return_value={"asOfDate":"2026-10-31","size":2,"fund":{"entity":[self.row(),self.row()]}}
        session.get.return_value=r
        with self.assertRaisesRegex(m.HoldingsError,"identical Vanguard raw row"):
            m._vanguard_raw_pages(session,"VEA","https://example.com",500)

    def test_alternate_pagination_mismatch_rejected(self):
        from unittest.mock import Mock
        rows=[self.row(),self.row(weight=60,shares=200)]
        with patch.object(m,"_vanguard_raw_pages",side_effect=[
            (rows,"2026-10-31",2,{"a","b"}),(rows,"2026-10-31",2,{"a","c"})]):
            with self.assertRaisesRegex(m.HoldingsError,"alternate pagination mismatch"):
                m._fetch_vanguard_pages(Mock(),"VEA","https://example.com")

if __name__=="__main__":unittest.main()
