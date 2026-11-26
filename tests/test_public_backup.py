import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backup import public_row,write_backup
from scripts.restore_supabase_backup import read_backup,restore_empty

class PublicBackupTests(unittest.TestCase):
    def setUp(self):
        self.row={"id":1,"ledger_data":[{"type":"Deposit","totalCashFlow":1}],
            "history_data":[{"date":"2026-11-26","assets":1,"valuation":{"version":"v2","ledger_fingerprint":"fixture","holdings":[]}}],
            "stock_meta":{},"settings":{"sheetUrl":"private","exchangeRate":32},
            "performance_attribution":{"private":True},"attribution_benchmark_policy":{"approved":True}}
    def test_public_projection_and_capture_preserved(self):
        r=public_row(self.row)
        self.assertEqual(r["history_data"],self.row["history_data"])
        self.assertEqual(r["settings"],{"exchangeRate":32})
        self.assertNotIn("performance_attribution",r)
        self.assertNotIn("attribution_benchmark_policy",r)
        self.row["ledger_data"][0]["api_key"]="fixture"
        with self.assertRaises(ValueError):public_row(self.row)
    def test_roundtrip_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)
            name=write_backup(self.row,p,datetime.fromisoformat("2026-11-26T12:00:00+08:00"))
            r,ok=read_backup(p,"2026-11-26")
            self.assertTrue(ok)
            self.assertEqual(r,public_row(self.row))
            (p/name).write_bytes(b"[]")
            with self.assertRaises(ValueError):read_backup(p,"2026-11-26")
    def test_restore_refuses_active_target(self):
        c=Mock()
        with self.assertRaises(ValueError):restore_empty(c,public_row(self.row),"")
        c.table.assert_not_called()
        c.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data={
            "id":1,"ledger_data":[{"type":"Deposit"}],"history_data":[],"stock_meta":{},"settings":{},"attribution_benchmark_policy":None}
        with self.assertRaises(ValueError):restore_empty(c,public_row(self.row),"RESTORE_EMPTY")
        c.table.return_value.update.assert_not_called()

if __name__=="__main__":unittest.main()
