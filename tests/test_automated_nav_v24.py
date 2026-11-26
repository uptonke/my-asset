import sys
import unittest
from pathlib import Path
from datetime import datetime
from copy import deepcopy
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from capture_private_nav import make_snapshot,inputs,CaptureBlocked
from build_performance_attribution import parse_inputs
from performance_pit_nav import validate_snapshot,build_pit
from performance_coverage import CoverageIssue
from performance_brinson import build_brinson

class AutomatedNavTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime.fromisoformat("2026-07-11T10:15:00+08:00")
        self.row={"history_data":[{"date":"2026-06-27","assets":100.,"cost":50.},{"date":"2026-07-04","assets":100.,"cost":50.}],
                  "ledger_data":[{"date":"2026-07-03","type":"Deposit","totalCashFlow":1000},
                   {"date":"2026-07-03","type":"Buy","ticker":"X","category":"台股","shares":5,"totalCashFlow":-500}]}
        self.p=pd.Series([100.,110.],index=pd.to_datetime(["2026-07-03","2026-07-09"]))
        self.market={"assets":{"X":{"price":self.p,"splits":[],"split_ratios":{},"foreign":False,"bucket":"taiwan_equity",
                         "source":"fixture","calendar":"XTAI","instrument_id":"X.TW","currency":"TWD"}},
                     "fx":pd.Series([32.],index=pd.to_datetime(["2026-07-09"]))}
    def snapshot(self):
        return make_snapshot(self.row,self.now,self.market)
    def test_completed_close_capture_and_immutable_inputs(self):
        original=deepcopy(self.row)
        record=self.snapshot()
        self.assertEqual(record["date"],"2026-07-11")
        self.assertEqual(record["assets"],1050)
        self.assertEqual(record["cost"],500)
        self.assertEqual(record["valuation"]["holdings"][0]["quote_as_of"],"2026-07-09")
        self.assertTrue(record["valuation"]["quote_dates_verified"])
        self.assertFalse(record["valuation"]["quote_timestamps_verified"])
        self.assertEqual(self.row,original)
        _,tx,_=parse_inputs(self.row)
        self.assertEqual(validate_snapshot(record,tx)["capture_mode"],"automated_completed_daily_marks")
        record["valuation"]["holdings"][0]["quote_as_of"]="2026-07-10"
        with self.assertRaisesRegex(ValueError,"session"):validate_snapshot(record,tx)
    def test_duplicate_future_and_same_day(self):
        record=self.snapshot()
        self.row["history_data"].append(record)
        self.assertIsNone(self.snapshot())
        self.row["history_data"].pop()
        self.row["ledger_data"].append({"date":"2026-07-11","type":"Deposit","totalCashFlow":1})
        with self.assertRaisesRegex(CaptureBlocked,"SAME_DAY"):self.snapshot()
        self.row["ledger_data"].pop()
        with self.assertRaisesRegex(CaptureBlocked,"BEFORE_COMPLETED"):make_snapshot(self.row,datetime.fromisoformat("2026-07-11T09:00:00+08:00"),self.market)
    def test_missing_mark_not_imputed(self):
        self.market["assets"]["X"]["price"]=self.p.iloc[:1]
        with self.assertRaises(CoverageIssue):self.snapshot()
    def test_negative_cash_and_ledger_fingerprint(self):
        record=self.snapshot()
        self.row["ledger_data"][0]["totalCashFlow"]=999
        _,tx,_=parse_inputs(self.row)
        with self.assertRaisesRegex(ValueError,"fingerprint"):validate_snapshot(record,tx)
        self.row["ledger_data"][0]["totalCashFlow"]=400
        with self.assertRaisesRegex(CaptureBlocked,"NEGATIVE_CASH"):self.snapshot()
    def test_two_auto_snapshots_and_benchmark(self):
        record=self.snapshot()
        now2=datetime.fromisoformat("2026-07-18T10:15:00+08:00")
        self.market["assets"]["X"]["price"]=pd.concat([self.p,pd.Series([120.],index=pd.to_datetime(["2026-07-17"]))])
        self.market["fx"]=pd.Series([32.,32.],index=pd.to_datetime(["2026-07-09","2026-07-17"]))
        r2=make_snapshot(self.row,now2,self.market)
        _,tx,_=parse_inputs(self.row)
        nav={pd.Timestamp(r["date"]):r["assets"] for r in (record,r2)}
        out,valid=build_pit([record,r2],tx,nav,{"1W":{"start":record["date"],"end":r2["date"]}})
        self.assertEqual(out["pair_count"],1)
        self.assertAlmostEqual(out["windows"]["1W"]["asset_pnl_twd"],50.)
        cfg={"weights":{"taiwan_equity":.6,"cash":.4},"currency":{"taiwan_equity":"TWD","cash":"USD"},"proxies":{"taiwan_equity":"0050.TW","cash":"BOXX"}}
        bprices={"taiwan_equity":self.market["assets"]["X"]["price"],"cash":pd.Series([1.,1.],index=pd.to_datetime(["2026-07-10","2026-07-17"]))}
        bf=build_brinson(valid,tx,nav,cfg,(bprices,self.market["fx"]))
        self.assertEqual(bf["status"],"OK_RESEARCH_ONLY",bf)
        self.assertAlmostEqual(bf["latest"]["identity_error_pp"],0.)

if __name__=="__main__":unittest.main()
