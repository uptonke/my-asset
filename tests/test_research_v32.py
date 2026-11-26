import sys
import json
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from build_performance_attribution import parse_inputs
from performance_pit_nav import ledger_fingerprint
from performance_cashflow import interval,classify
from performance_quality_gate import quality_gate
from performance_quality_diagnostics import diagnostics
from performance_risk_research import regime,proxy_model,variance_shares,actual_factor_budget,run_research
from cost_walk_forward import CONFIG,OPT,simulate

class AttributionTests(unittest.TestCase):
    def test_metadata_preserves_fingerprint_and_cash_identity(self):
        h=[{"date":"2026-01-01","assets":1000},{"date":"2026-01-08","assets":1040}]
        ledger=[{"date":"2026-01-01","type":"Buy","ticker":"VOO","category":"美股","shares":1,"totalCashFlow":-100},
            {"date":"2026-01-02","type":"Income","totalCashFlow":20},
            {"date":"2026-01-03","type":"Expense","totalCashFlow":-5},
            {"date":"2026-01-04","type":"Income","totalCashFlow":5}]
        nav,old,cats=parse_inputs({"history_data":h,"ledger_data":ledger})
        ledger[1]["cashflow_detail"]={"kind":"dividend","ticker":"VOO"}
        ledger[2]["cashflow_detail"]={"kind":"fee"}
        _,tx,_=parse_inputs({"history_data":h,"ledger_data":ledger})
        self.assertEqual(ledger_fingerprint(old),ledger_fingerprint(tx))
        p={"start":"2026-01-01","end":"2026-01-08","explicit_other_cashflow_twd":20,
            "actual_pnl_twd":40,"asset_pnl_twd":15,"unexplained_twd":5,"rows":[{"ticker":"VOO","pnl_twd":15}]}
        r=interval(nav,tx,cats,p)
        self.assertEqual(r["linked_dividend_twd"],20)
        self.assertEqual(r["unclassified_income_twd"],5)
        self.assertEqual(r["asset_including_linked_dividend_twd"],35)
        self.assertEqual(r["other_after_dividend_twd"],0)
        self.assertEqual(r["identity_error_twd"],0)
        self.assertEqual(classify({**tx[1],"cashflow_detail":{"kind":"dividend","ticker":"UNKNOWN"}},cats)[0],"dividend_unlinked")
        self.assertEqual(classify({**tx[2],"cashflow_detail":{"kind":"dividend","ticker":"VOO"}},cats)[2],"INVALID_METADATA")
    def test_quality_segments_do_not_cross_gap(self):
        dates=pd.date_range("2026-01-01",periods=5,freq="7D")
        nav={d:1000. for d in dates}
        def row(i,gap):
            return {"start":str(dates[i].date()),"end":str(dates[i+1].date()),"start_nav_gap_twd":gap,"end_nav_gap_twd":0.,
                "portfolio_return_pct":0.,"benchmark_return_pct":0.,"active_return_pp":0.,
                "effects_pp":{"allocation":0.,"selection":0.,"interaction":0.,"execution_other":0.,"nav_bridge":0.},
                "rows":[{"bucket":"cash","allocation_pp":0.,"selection_pp":0.,"interaction_pp":0.}]}
        h={"periods":[row(0,0),row(1,20),row(3,0)],"skipped":[{"start":str(dates[2].date()),"end":str(dates[3].date()),"diagnostics":{"issues":[{"code":"NEGATIVE_CASH"}]}}],"benchmark":{"weights":{"cash":1.}}}
        gate=quality_gate(nav,h,{}, {},{})
        r=diagnostics(nav,[],h,{},gate)
        self.assertEqual(r["windows"]["4"]["expected"],4)
        self.assertEqual(r["windows"]["4"]["passed"],2)
        self.assertEqual(len(r["quality_segments"]),2)
        self.assertEqual(r["reason_counts"]["NEGATIVE_CASH"],1)
        self.assertEqual(r["priority"][0]["status"],"EXCLUDED")

class RiskTests(unittest.TestCase):
    def setUp(self):
        self.cfg=json.loads(CONFIG.read_text());self.cfg.update(training_observations=70,holding_observations=10)
        self.opt=json.loads(OPT.read_text())
        self.cols=[x["ticker"] for x in self.cfg["universe"]]
        rng=np.random.default_rng(83)
        returns=rng.normal(.0004,.011,(103,len(self.cols)))
        self.prices=pd.DataFrame(100*np.cumprod(1+returns,axis=0),columns=self.cols,index=pd.bdate_range("2024-01-01",periods=103))
    def test_risk_variance_identity(self):
        t=self.prices.pct_change(fill_method=None).dropna().iloc[:70]
        B,F,S=proxy_model(t)
        w=np.array([x["weight"] for x in self.cfg["universe"]])
        shares,var,_=variance_shares(w,B,F,S)
        self.assertAlmostEqual(shares.sum(),1.)
        self.assertAlmostEqual(var,float((t.to_numpy()@w).var(ddof=1)),places=12)
        self.assertIn(regime(t)["regime"],("RISK_ON","NEUTRAL","RISK_OFF"))
    def test_walk_forward_no_lookahead(self):
        methods=("strategic_rebalance","regime_aware","factor_budget")
        r=simulate(self.prices,self.cfg,self.opt,1.,methods=methods)
        first=r["folds"][0]
        self.assertLess(first["train_end"],first["execution_date"])
        self.assertLess(first["execution_date"],first["test_start"])
        changed=self.prices.copy()
        changed.loc[first["test_start"]:,self.cols[0]]*=1.15
        other=simulate(changed,self.cfg,self.opt,1.,methods=methods)["folds"][0]
        for m in methods:
            np.testing.assert_allclose(list(first["methods"][m]["target_weights"].values()),list(other["methods"][m]["target_weights"].values()),atol=1e-8)
            self.assertLessEqual(r["aggregate"][m]["net_return_pct"],r["aggregate"][m]["gross_return_pct"]+1e-8)
        self.assertEqual(first["methods"]["regime_aware"]["model"]["regime"],other["methods"]["regime_aware"]["model"]["regime"])
        successful=[f["methods"]["factor_budget"] for f in r["folds"] if f["methods"]["factor_budget"]["status"]=="OK"]
        self.assertTrue(successful)
        for s in successful:self.assertAlmostEqual(sum(x["candidate_pct"] for x in s["model"]["risk_shares"]),100.,places=8)
    def test_actual_factor_budget(self):
        rng=np.random.default_rng(21);n=60;f=["A","B"]
        p=pd.DataFrame(rng.normal(0,.02,(n,2)),columns=f)
        p["start"]=pd.date_range("2024-01-01",periods=n,freq="7D");p["end"]=p["start"]+pd.Timedelta(days=7)
        p["RF"]=.001;p["usd"]=p["RF"]+p["A"]+.5*p["B"]+rng.normal(0,.005,n)
        out=actual_factor_budget(p,f)
        self.assertEqual(out["status"],"RESEARCH_ONLY")
        self.assertAlmostEqual(sum(x["risk_pct"] for x in out["rows"]),100.,places=8)
        self.assertFalse(out["execution_permission"])

if __name__=="__main__":unittest.main()
