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

if __name__=="__main__":unittest.main()
