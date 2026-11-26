import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from performance_calendar import required_session,fund_holiday_calendar
from performance_coverage import quote,CoverageIssue,cash_trace,asset_mark
from performance_market_data import merge_verified_fund_history,recover_fund_history,apply_fund_archive,merge_fund_archive,FUND_CODES

class MarketRecoveryTests(unittest.TestCase):
    def test_twse_emergency_closure(self):
        s=pd.Series([100.],index=pd.to_datetime(["2026-07-09"]))
        for d in pd.to_datetime(["2026-07-10","2026-07-11","2026-07-12"]):
            self.assertEqual(required_session("XTAI",d),pd.Timestamp("2026-07-09"))
            self.assertEqual(quote(s,d,7,"TW","fixture",calendar="XTAI"),100.)
        with self.assertRaises(CoverageIssue):
            quote(s,pd.Timestamp("2026-07-13"),7,"TW","fixture",calendar="XTAI")
    def test_domestic_fund_verified_holiday(self):
        d=pd.Timestamp("2026-02-21")
        p=pd.Series([100.],index=pd.to_datetime(["2026-02-11"]))
        m={"assets":{"安聯台灣科技":{"price":p,"fund":True,"splits":[],"foreign":False,"source":"fixture"}}}
        self.assertEqual(asset_mark("安聯台灣科技",2,d,m),(200.,False))
        self.assertIsNone(fund_holiday_calendar("OTHER",d))
        self.assertIsNone(fund_holiday_calendar("安聯台灣科技",pd.Timestamp("2026-02-23")))
        with self.assertRaises(CoverageIssue):
            asset_mark("安聯台灣科技",2,pd.Timestamp("2026-02-23"),m)
    def test_twse_lunar_new_year(self):
        d=pd.Timestamp("2026-02-21")
        self.assertEqual(required_session("XTAI",d),pd.Timestamp("2026-02-11"))
        s=pd.Series([100.],index=pd.to_datetime(["2026-02-11"]))
        self.assertEqual(quote(s,d,7,"TW","fixture",calendar="XTAI"),100.)
        with self.assertRaises(CoverageIssue) as ctx:
            quote(s,pd.Timestamp("2026-02-23"),7,"TW","fixture",calendar="XTAI")
        self.assertEqual(ctx.exception.detail["expected_session"],"2026-02-23")
    def test_us_holiday_and_missing_trading_day(self):
        s=pd.Series([100.],index=pd.to_datetime(["2025-07-03"]))
        self.assertEqual(quote(s,pd.Timestamp("2025-07-05"),7,"US","fixture",calendar="XNYS"),100.)
        with self.assertRaises(CoverageIssue):
            quote(s,pd.Timestamp("2025-07-07"),7,"US","fixture",calendar="XNYS")
    def test_no_future_quote_or_wrong_calendar(self):
        s=pd.Series([100.],index=pd.to_datetime(["2026-02-23"]))
        with self.assertRaises(CoverageIssue):
            quote(s,pd.Timestamp("2026-02-21"),7,"TW","fixture",calendar="XTAI")
        with self.assertRaises(CoverageIssue):
            quote(s,pd.Timestamp("2026-02-23"),7,"TW","fixture",calendar="UNKNOWN")
    def test_cash_trace_preserves_deficit(self):
        tx=[{"date":pd.Timestamp("2025-01-01"),"flow":-2.},
            {"date":pd.Timestamp("2025-01-02"),"flow":1.85}]
        r=cash_trace(tx)
        self.assertEqual(r["material_negative_days"],1)
        self.assertEqual(r["minimum_cash_twd"],-2.)
        self.assertAlmostEqual(r["negative_days"][-1]["cash_twd"],-.15)
        self.assertFalse(r["opening_cash_verified"])
    def test_supplied_archive(self):
        path=Path(__file__).resolve().parents[1]/"data/attribution/fund_nav_history.csv"
        self.assertTrue(path.is_file())
        for ticker in FUND_CODES:
            archive=merge_fund_archive(ticker,pd.Series(dtype=float),path)
            self.assertEqual(len(archive),424)
            self.assertEqual(str(archive.index[0].date()),"2025-03-03")
            self.assertEqual(str(archive.index[-1].date()),"2026-11-25")
            reference=archive.iloc[-89:]
            merged,status,error=apply_fund_archive(ticker,reference,path)
            self.assertEqual(status,"ARCHIVE_VERIFIED_OVERLAP")
            self.assertIsNone(error)
            pd.testing.assert_series_equal(merged,archive)
            merged,status,error=apply_fund_archive(ticker,reference*1.02,path)
            self.assertEqual(status,"ARCHIVE_REJECTED")
            pd.testing.assert_series_equal(merged,reference*1.02)
            _,status,_=apply_fund_archive(ticker,pd.Series(dtype=float),path)
            self.assertEqual(status,"ARCHIVE_REJECTED")
    def test_verified_fund_overlap(self):
        dates=pd.date_range("2025-01-01",periods=10)
        candidate=pd.Series(range(10,20),index=dates,dtype=float)
        ref=candidate.iloc[5:]
        self.assertEqual(len(merge_verified_fund_history(ref,candidate,"TWD",{})),10)
        with self.assertRaises(ValueError):merge_verified_fund_history(ref,candidate*1.02,"TWD",{})
        with self.assertRaises(ValueError):merge_verified_fund_history(ref,candidate,"USD",{})
        with self.assertRaises(ValueError):merge_verified_fund_history(ref.iloc[1:],candidate,"TWD",{})
        with self.assertRaises(ValueError):merge_verified_fund_history(ref,candidate,"TWD",{dates[1]:2})
        with patch("performance_market_data.yahoo_chart",return_value=(candidate,{},"TWD")):
            merged,source=recover_fund_history("統一黑馬",ref,dates[0])
            self.assertEqual(len(merged),10)
            self.assertTrue(source.startswith("F0HKG05X0O"))
        with patch("performance_market_data.yahoo_chart",side_effect=ValueError):
            merged,source=recover_fund_history("統一黑馬",ref,dates[0])
            self.assertIsNone(source)
            pd.testing.assert_series_equal(merged,ref)

if __name__=="__main__":unittest.main()
