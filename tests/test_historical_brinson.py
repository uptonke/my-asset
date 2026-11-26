import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from performance_brinson_historical import active_link,build_historical


class HistoricalBrinsonTests(unittest.TestCase):
    def setUp(self):
        self.a,self.b,self.c=pd.to_datetime(["2025-01-02","2025-01-09","2025-01-16"])
        self.d=self.a+pd.Timedelta(days=3)
        dates=[self.a,self.d,self.b,self.c]
        self.p=pd.Series([10.,11.,12.,13.],index=dates)
        self.flat=pd.Series([1.]*4,index=dates)
        self.config={"weights":{"global_equity":.6,"cash":.4},"currency":{"global_equity":"TWD","cash":"TWD"},"approved":False}
        self.market={"assets":{"X":{"price":self.p,"splits":[],"foreign":False,"bucket":"global_equity"}},"fx":self.flat}
        self.bmarket=({"global_equity":self.p,"cash":self.flat},self.flat)
        self.tx=[{"date":self.a,"qty":0.,"flow":100.,"type":"deposit","ticker":""},
                 {"date":self.a,"qty":5.,"flow":-50.,"type":"buy","ticker":"X"}]
    def run_report(self,nav,tx=None,market=None):
        return build_historical(nav,tx if tx is not None else self.tx,{"X":"美股"},market or self.market,self.config,self.bmarket)
    def test_equal_returns_limit_and_compounding(self):
        p,b,c=active_link([.1,.2],[.1,-.1],[[0.,0.],[.2,.1]])
        self.assertAlmostEqual(p,.32)
        self.assertAlmostEqual(b,-.01)
        self.assertAlmostEqual(sum(c),p-b)
    def test_no_trade_and_nav_bridge(self):
        r=self.run_report({self.a:100.,self.b:112.,self.c:117.})
        self.assertEqual(r["eligible_intervals"],2)
        self.assertAlmostEqual(r["periods"][0]["effects_pp"]["nav_bridge"],2.)
        s=r["latest_segment"]
        self.assertAlmostEqual(sum(s["effects_pp"].values()),s["active_return_pp"])
        self.assertAlmostEqual(s["portfolio_return_pct"],17.)
    def test_trade_and_external_flow(self):
        tx=self.tx+[{"date":self.d,"qty":1.,"flow":-12.,"type":"buy","ticker":"X"},
                    {"date":self.d,"qty":0.,"flow":20.,"type":"deposit","ticker":""}]
        r=self.run_report({self.a:100.,self.b:130.},tx)
        self.assertEqual(r["eligible_intervals"],1)
        p=r["latest"]
        self.assertEqual(p["subperiod_count"],2)
        self.assertLess(p["effects_pp"]["execution_other"],0.)
        self.assertAlmostEqual(sum(p["effects_pp"].values()),p["active_return_pp"])
        self.assertAlmostEqual(p["benchmark_return_pct"],12.)
    def test_quarantined_holding_not_imputed(self):
        r=self.run_report({self.a:100.,self.b:110.},market={**self.market,"quarantined":{"X":"conflict"}})
        self.assertEqual(r["eligible_intervals"],0)
        self.assertIn("Quarantined",r["skipped"][0]["reason"])
    def test_missing_price_breaks_link(self):
        d=self.c+pd.Timedelta(days=14);e=d+pd.Timedelta(days=7);f=e+pd.Timedelta(days=7)
        m={**self.market,"assets":{"X":{**self.market["assets"]["X"],"price":pd.concat([self.p,pd.Series([14.,15.],index=[e,f])])}}}
        bm=({"global_equity":pd.concat([self.p,pd.Series([14.,15.],index=[e,f])]),"cash":pd.concat([self.flat,pd.Series([1.,1.],index=[e,f])])},self.flat)
        r=build_historical({self.a:100.,self.b:110.,d:120.,e:120.,f:125.},self.tx,{"X":"美股"},m,self.config,bm)
        self.assertEqual(len(r["segments"]),2)
        self.assertEqual(r["latest_segment"]["start"],str(e.date()))
        self.assertEqual(r["eligible_intervals"],2)


if __name__=="__main__":unittest.main()
