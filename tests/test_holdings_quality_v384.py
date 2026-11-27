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

if __name__=="__main__":unittest.main()
