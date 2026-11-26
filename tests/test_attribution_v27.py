import sys
import unittest
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch,Mock
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from performance_total_return import policy_config,build_total_return,adjusted_benchmark_prices
from performance_brinson_historical import build_historical
from performance_quality_gate import interval_quality,quality_gate
from private_portfolio_backup import encrypt_row,decrypt_row,recover_row,private_bucket

class TotalReturnTests(unittest.TestCase):
    def setUp(self):
        self.a,self.b=pd.to_datetime(["2026-07-18","2026-07-25"])
        self.nav={self.a:1000.,self.b:1010.}
        self.tx=[{"date":self.a,"type":"deposit","ticker":"","qty":0.,"flow":1000.},
                 {"date":self.b,"type":"income","ticker":"","qty":0.,"flow":10.}]
        self.cfg=policy_config({})
        dates=pd.to_datetime(["2026-07-17","2026-07-24"])
        self.fx=pd.Series([32.,32.],index=dates)
        self.flat=pd.Series([100.,100.],index=dates)
        self.bm={g:self.flat.copy() for g in self.cfg["weights"]}
        self.market={"assets":{},"fx":self.fx}
    def test_adjusted_benchmark_comparison_no_double_count(self):
        p=build_historical(self.nav,self.tx,{},self.market,self.cfg,(self.bm,self.fx))
        b=dict(self.bm)
        b["global_equity"]=pd.Series([100.,102.],index=self.flat.index)
        r=build_total_return(self.nav,self.tx,{},self.market,{},p,(b,self.fx))
        self.assertEqual(r["eligible_intervals"],1,r)
        self.assertAlmostEqual(r["latest_segment"]["portfolio_return_pct"],1.)
        self.assertAlmostEqual(r["latest_segment"]["benchmark_return_pct"],1.2)
        self.assertAlmostEqual(r["matched_price_comparison"][0]["distribution_adjustment_pp"],1.2)
        self.assertAlmostEqual(sum(r["latest_segment"]["effects_pp"].values()),-.2)
        self.assertFalse(r["execution_permission"])
        self.assertAlmostEqual(r["calibration"]["one_way_distance_pct"],90.)
    def test_policy_prospective_and_no_fallback(self):
        w=self.cfg["weights"]
        now=datetime(2026,7,18,10,tzinfo=timezone.utc)
        policy={"approved":True,"approved_at":"2026-07-18T00:00:00+00:00","effective_date":"2026-07-17","weights":w}
        with self.assertRaises(ValueError):policy_config({"attributionBenchmarkPolicy":policy},now)
        policy["effective_date"]="2026-07-25"
        self.assertTrue(policy_config({"attributionBenchmarkPolicy":policy},now)["approved"])
        with patch("performance_total_return.yahoo_chart",side_effect=ValueError):
            self.assertEqual(build_total_return(self.nav,self.tx,{},self.market,{},{} )["status"],"UNAVAILABLE")
    def test_adjusted_source_flags(self):
        with patch("performance_total_return.yahoo_chart",side_effect=lambda symbol,earliest,adjusted=False:(self.flat,{},"TWD" if symbol in ("0050.TW","TWD=X") else "USD")) as mock:
            adjusted_benchmark_prices(self.cfg,self.a)
            calls=mock.call_args_list
            self.assertEqual(sum(c.kwargs.get("adjusted",False) for c in calls),4)
    def test_gate_blocks_formal_use(self):
        r={"start":str(self.a.date()),"end":str(self.b.date()),"start_nav_gap_twd":20.,"end_nav_gap_twd":0.,
           "effects_pp":{"nav_bridge":.6},"active_return_pp":.6,"data_quality":{"micro_cash_tolerance_used":True}}
        q=interval_quality(r,self.nav)
        self.assertEqual(set(q["reasons"]),{"NAV_GAP","METHOD_BRIDGE","MICRO_CASH"})
        g=quality_gate(self.nav,{"periods":[r]}, {}, {"snapshots":[{"status":"INVALID"}]}, {})
        self.assertEqual(g["screen_pass_intervals"],0)
        self.assertFalse(g["formal_attribution_permission"])
        self.assertIn("INVALID_CAPTURED_SNAPSHOT",g["reasons"])

class BackupTests(unittest.TestCase):
    def setUp(self):
        self.key=b"x"*32
        self.row={"id":1,"ledger_data":[{"type":"Deposit","totalCashFlow":1000}],"history_data":[{"date":"2026-07-18","valuation":{"version":"v2"}}],"stock_meta":{},"settings":{},"attribution_benchmark_policy":None}
    def test_encryption_authenticated_roundtrip(self):
        b=encrypt_row(self.row,self.key)
        self.assertEqual(decrypt_row(b,self.key),self.row)
        self.assertNotEqual(b,encrypt_row(self.row,self.key))
        self.assertNotIn(b"ledger_data",b)
        with self.assertRaises(Exception):decrypt_row(b,b"y"*32)
        with self.assertRaises(Exception):decrypt_row(b[:-1]+bytes([b[-1]^1]),self.key)
    def test_empty_restore_guard(self):
        client=Mock()
        with patch.dict("os.environ",{"PORTFOLIO_ROW_ID":"1"}):
            recover_row(client,self.row,"verify","")
            client.rpc.assert_not_called()
            with self.assertRaises(ValueError):recover_row(client,self.row,"restore-empty","")
            client.rpc.assert_not_called()
            client.rpc.return_value.execute.return_value.data=False
            with self.assertRaises(ValueError):recover_row(client,self.row,"restore-empty","RESTORE_EMPTY")
            client.rpc.assert_called_once()
    def test_public_bucket_rejected(self):
        client=Mock()
        client.storage.get_bucket.return_value={"public":True}
        with self.assertRaises(ValueError):private_bucket(client)
        client.storage.from_.assert_not_called()

if __name__=="__main__":unittest.main()
