import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from build_performance_attribution import asset_pnl,window_pnl,carino,parse_inputs,factor_report,FACTORS,ENGINE_VERSION

class AttributionTests(unittest.TestCase):
    def setUp(self):
        self.a,self.b,self.c=pd.to_datetime(["2025-01-04","2025-01-08","2025-01-11"])
        self.price=pd.Series([10.,12.,11.],index=[self.a,self.b,self.c])
        self.fx=pd.Series([30.,32.,31.],index=[self.a,self.b,self.c])
        self.tx=[{"date":self.a,"ticker":"X","qty":10.,"flow":-3000.,"type":"buy"},
                 {"date":self.b,"ticker":"X","qty":-4.,"flow":1530.,"type":"sell"}]
    def test_trade_and_currency_identity(self):
        r=asset_pnl("X",self.tx,self.a,self.c,self.price,self.fx,True,[])
        self.assertAlmostEqual(r["pnl_twd"],6*11*31-3000+1530)
        self.assertAlmostEqual(sum(r[k] for k in ["price_twd","fx_twd","interaction_twd","execution_vs_close_twd"]),r["pnl_twd"])
        self.assertAlmostEqual(r["execution_vs_close_twd"],-6.)
    def test_split_blocks(self):
        with self.assertRaisesRegex(ValueError,"Split"):
            asset_pnl("X",self.tx,self.a,self.c,self.price,self.fx,True,[self.b])
    def test_missing_keeps_residual(self):
        nav={self.a:5000.,self.c:5500.}
        m={"assets":{},"fx":self.fx}
        r=window_pnl(nav,self.tx,{"X":"US"},m,self.a,self.c)
        self.assertEqual(r["status"],"PARTIAL")
        self.assertEqual(r["unexplained_twd"],500.)
        self.assertEqual(len(r["missing"]),1)
    def test_external_flow_not_pnl(self):
        tx=self.tx+[{"date":self.b,"ticker":"","qty":0.,"flow":1000.,"type":"deposit"}]
        m={"assets":{"X":{"price":self.price,"foreign":True,"splits":[],"bucket":"global_equity","source":"test"}},"fx":self.fx}
        r=window_pnl({self.a:5000.,self.c:6500.},tx,{"X":"US"},m,self.a,self.c)
        self.assertEqual(r["actual_pnl_twd"],500.)
        self.assertAlmostEqual(r["asset_pnl_twd"]+r["unexplained_twd"],500.)
    def test_carino_zero_and_compounding(self):
        r=np.array([.10,-.05,0.])
        c=np.array([[.07,.03],[-.02,-.03],[.01,-.01]])
        total,linked=carino(r,c)
        self.assertAlmostEqual(total,.045)
        self.assertAlmostEqual(linked.sum(),total)
        total,linked=carino([.25,-.2],[[.1,.15],[-.1,-.1]])
        self.assertAlmostEqual(total,0.)
        self.assertAlmostEqual(linked.sum(),0.)
        with self.assertRaises(ValueError):carino([.1],[[.05]])
    def test_factor_fit_and_link(self):
        rng=np.random.default_rng(123)
        n=65
        ends=pd.date_range("2024-01-13",periods=n,freq="7D")
        f=rng.normal(0,.02,(n,8));ru=.001+f@np.arange(1,9)/10+rng.normal(0,.001,n)
        fx=rng.normal(0,.005,n);rt=(1+ru)*(1+fx)-1
        p=pd.DataFrame(f,columns=FACTORS)
        p["start"]=ends-pd.Timedelta(days=7);p["end"]=ends;p["usd"]=ru;p["twd"]=rt;p["fx"]=fx;p["RF"]=.0005
        nav={d:100. for d in [p.iloc[0]["start"]]+list(ends)}
        result=factor_report(p,[],nav)
        self.assertEqual(result["status"],"OK")
        self.assertAlmostEqual(sum(result["windows"]["SI"]["contributions_pp"].values()),result["windows"]["SI"]["total_return_pct"])
        self.assertAlmostEqual(result["windows"]["1W"]["total_return_pct"],rt[-1]*100)
        p=p.drop(index=30)
        result=factor_report(p,[],nav)
        self.assertNotIn("SI",result["windows"])
    def test_changed_category_does_not_block_other_assets(self):
        row={"history_data":[{"date":"2025-01-01","assets":100},{"date":"2025-01-08","assets":110}],
             "ledger_data":[{"date":"2025-01-01","ticker":"X","type":"Buy","shares":1,"totalCashFlow":-10,"category":"TW"},
                            {"date":"2025-01-02","ticker":"X","type":"Buy","shares":1,"totalCashFlow":-10,"category":"US"}]}
        _,_,cats=parse_inputs(row)
        self.assertEqual(cats["X"],"__AMBIGUOUS__")
    def test_duplicate_nav_rejected(self):
        with self.assertRaisesRegex(ValueError,"duplicate"):
            parse_inputs({"history_data":[{"date":"2025-01-01","assets":1},{"date":"2025-01-01","assets":2}]})
class RefreshGuardTests(unittest.TestCase):
    def setUp(self):
        from datetime import datetime, timezone
        self.now = datetime(2026,11,26,tzinfo=timezone.utc)
        self.row = {"history_data":[{"date":"2026-11-14","assets":100},{"date":"2026-11-21","assets":90}],
                    "ledger_data":[],
                    "performance_attribution":{"version":"v1.0","engine_version":ENGINE_VERSION,"nav_as_of":"2026-11-21","ledger_count":0,"history_count":2,
                        "generated_at":"2026-11-25T00:00:00+00:00","pnl":{"1W":{}},"factor":{"status":"OK"}}}
    def reason(self):
        from build_performance_attribution import refresh_reason
        return refresh_reason(self.row,self.now)
    def test_fresh_skips(self):
        self.assertIsNone(self.reason())
    def test_invalidated_rebuilds(self):
        self.row["performance_attribution"]=None
        self.assertEqual(self.reason(),"missing_or_invalidated")
    def test_changed_nav_rebuilds(self):
        self.row["history_data"].append({"date":"2026-11-24","assets":95})
        self.assertEqual(self.reason(),"source_mismatch")
    def test_weekly_refresh(self):
        self.row["performance_attribution"]["generated_at"]="2026-11-19T00:00:00+00:00"
        self.assertEqual(self.reason(),"weekly_source_refresh")
    def test_factor_error_retry(self):
        self.row["performance_attribution"]["factor"]["status"]="UNAVAILABLE"
        self.assertEqual(self.reason(),"retry_factor_source")
    def test_invalid_timestamp(self):
        self.row["performance_attribution"]["generated_at"]="bad"
        self.assertEqual(self.reason(),"invalid_report_metadata")

class QualityTests(unittest.TestCase):
    def test_split_inference(self):
        from performance_data_quality import split_basis
        from build_performance_attribution import close
        a,b,c=pd.to_datetime(["2025-01-02","2025-02-03","2025-03-03"])
        price=pd.Series([25.,26.],index=[a,c])
        tx=[{"date":a,"qty":10.,"flow":-1000.},{"date":c,"qty":-40.,"flow":1040.}]
        chosen,basis=split_basis(tx,{b:4.},price,None,False,close)
        self.assertEqual(basis,"inferred_as_traded_converted")
        self.assertEqual(chosen[0]["qty"],40.)
        self.assertEqual(tx[0]["qty"],10.)
        normalized=[{"date":a,"qty":40.,"flow":-1000.},tx[1]]
        self.assertEqual(split_basis(normalized,{b:4.},price,None,False,close)[1],"inferred_already_split_normalized")
    def test_quarantine_and_cash(self):
        from performance_data_quality import reconcile_transactions,cash_reconciliation
        from build_performance_attribution import close
        a,b,c=pd.to_datetime(["2025-01-02","2025-02-03","2025-03-03"])
        tx=[{"date":a,"ticker":"X","qty":2.,"flow":-20.,"type":"buy"},{"date":b,"ticker":"X","qty":-3.,"flow":30.,"type":"sell"}]
        m={"assets":{},"fx":None}
        adjusted,diag,excluded=reconcile_transactions(tx,{"X":"TW"},m,close)
        self.assertEqual(diag[0]["raw_inventory"]["ending_shares"],-1.)
        m["quarantined"]=excluded
        nav={b:100.,c:95.}
        p=window_pnl(nav,adjusted,{"X":"TW"},m,b,c)
        self.assertEqual(p["historical_issues_no_window_trades"],["X"])
        self.assertEqual(p["unexplained_twd"],-5.)
        r=cash_reconciliation(nav,tx,{"1M":p})["1M"]
        self.assertFalse(r["opening_cash_balance_verified"])
        self.assertAlmostEqual(r["bridge_error_twd"],0.)
if __name__=="__main__":unittest.main()
