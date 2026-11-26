import sys
import unittest
import tempfile
from pathlib import Path
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from performance_brinson_historical import build_historical
from import_fund_nav_archive import import_archive
from performance_market_data import FUND_CODES

class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.a,self.d,self.b=pd.to_datetime(["2025-01-01","2025-01-04","2025-01-08"])
        self.p=pd.Series([10.,12.],index=[self.a,self.b])
        self.flat=pd.Series([1.,1.],index=[self.a,self.b])
        self.cfg={"weights":{"taiwan_equity":.6,"cash":.4},"currency":{"taiwan_equity":"TWD","cash":"TWD"}}
        self.market={"assets":{"X":{"price":self.p,"splits":[],"split_ratios":{},"foreign":False,"bucket":"taiwan_equity","source":"fixture"}},"fx":self.flat}
        self.bm=({"taiwan_equity":self.p,"cash":self.flat},self.flat)
    def report(self,tx,market=None,cats=None):
        return build_historical({self.a:100.,self.b:110.},tx,cats or {"X":"台股"},market or self.market,self.cfg,self.bm)
    def tx(self,cash):
        return [{"date":self.a,"qty":0.,"flow":cash+100,"type":"deposit","ticker":""},
                {"date":self.a,"qty":10.,"flow":-100.,"type":"buy","ticker":"X","category":"台股"}]
    def test_micro_cash(self):
        r=self.report(self.tx(-.15))
        self.assertEqual(r["eligible_intervals"],1)
        self.assertEqual(r["coverage_diagnostics"]["micro_cash_intervals"],1)
        self.assertAlmostEqual(r["latest"]["data_quality"]["minimum_ledger_cash_twd"],-.15)
    def test_multiple_blockers(self):
        m={**self.market,"assets":{"X":{**self.market["assets"]["X"],"price":pd.Series(dtype=float)}}}
        r=self.report(self.tx(-2),m)
        self.assertEqual(r["eligible_intervals"],0)
        self.assertEqual(r["coverage_diagnostics"]["reason_interval_counts"]["NEGATIVE_CASH"],1)
        self.assertEqual(r["coverage_diagnostics"]["reason_interval_counts"]["MISSING_PRICE"],1)
        self.assertTrue(any(z["ticker"]=="X" for z in r["skipped"][0]["diagnostics"]["issues"]))
    def test_verified_subscription(self):
        tx=self.tx(10)
        tx[1]["subscription"]={"verified":True,"paid_date":str(self.a.date()),"first_valuation_date":str(self.d.date()),"evidence_ref":"synthetic"}
        m={**self.market,"assets":{"X":{**self.market["assets"]["X"],"price":pd.Series([10.,12.],index=[self.d,self.b])}}}
        r=self.report(tx,m)
        self.assertEqual(r["eligible_intervals"],1)
        self.assertEqual(r["coverage_diagnostics"]["pending_subscription_intervals"],1)
        self.assertEqual(r["latest"]["subperiod_count"],2)
        tx[1]["subscription"]["verified"]=False
        r=self.report(tx,m)
        self.assertEqual(r["eligible_intervals"],0)
        self.assertIn("SUBSCRIPTION_UNVERIFIED",r["coverage_diagnostics"]["reason_interval_counts"])
    def test_no_automatic_cost_fallback(self):
        m={**self.market,"assets":{"X":{**self.market["assets"]["X"],"price":pd.Series([12.],index=[self.b])}}}
        r=self.report(self.tx(10),m)
        self.assertEqual(r["eligible_intervals"],0)
        self.assertIn("BEFORE_FIRST_QUOTE",r["coverage_diagnostics"]["reason_interval_counts"])
    def test_archive_import(self):
        t=next(iter(FUND_CODES))
        with tempfile.TemporaryDirectory() as d:
            inp=Path(d)/"in.csv";out=Path(d)/"out.csv"
            data=pd.DataFrame([{"ticker":t,"fund_id":FUND_CODES[t][0],"currency":"TWD","date":"2025-01-01","nav":10,"source":"synthetic"}])
            data.to_csv(inp,index=False)
            self.assertEqual(import_archive([inp],out),1)
            data["nav"]=11
            data.to_csv(inp,index=False)
            with self.assertRaisesRegex(ValueError,"Conflicting"):import_archive([inp],out)
            self.assertEqual(pd.read_csv(out).nav.iloc[0],10)

if __name__=="__main__":unittest.main()
