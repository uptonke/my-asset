import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from performance_currency_rebalance import (currency_parts,currency_risk,recorded_currency_pnl,
    rebalance_report,solve_candidates,candidate_report,CONFIG,OPT)
from performance_portfolio_risk import CASH,BUCKETS
from run_constrained_optimizer import constraint_matrix,feasibility,POLICY
import json

class CurrencyRebalanceTests(unittest.TestCase):
    def setUp(self):
        self.dates=pd.date_range("2025-01-01",periods=53,freq="7D")
        rng=np.random.default_rng(31)
        cols=["A","B","C","TW","BTC","GOLD","BOXX",CASH]
        buckets=["global_equity"]*3+["taiwan_equity","crypto","gold","cash","cash"]
        weights=[.18,.18,.17,.15,.15,.05,.10,.02]
        self.ex={"as_of":"2026-01-01","basis":"RECONSTRUCTED_LEDGER","model_nav_twd":100000.,
            "nav_gap_pct":0.,"later_ledger_events":0,"warnings":[],
            "holdings":[{"ticker":t,"bucket":g,"weight":w,"market_value_twd":w*100000.,
                         "currency":"TWD" if t in ("TW",CASH) else "USD"} for t,g,w in zip(cols,buckets,weights)]}
        local=rng.normal(0,.02,(52,8));local[:,4]*=3;local[:,5]*=.7;local[:,6]*=.05;local[:,7]=0.
        f=rng.normal(0,.006,52);self.fx=pd.Series(32*np.r_[1.,np.cumprod(1+f)],index=self.dates)
        usd=np.array([t not in ("TW",CASH) for t in cols])
        self.returns=pd.DataFrame((1+local)*(1+f[:,None]*usd)-1,index=self.dates[1:],columns=cols)
        self.cfg=json.loads(CONFIG.read_text());self.opt=json.loads(OPT.read_text())
        self.scenarios=[{"id":"fx","label":"FX","local_price_shocks":dict.fromkeys(BUCKETS,0.),"usd_twd_shock":-.1}]
    def test_currency_identity(self):
        X,L,F,I=currency_parts(self.returns,self.ex,self.fx)
        np.testing.assert_allclose(L+F+I,X,atol=1e-12)
        self.assertTrue(np.all(F[:,3]==0))
        self.assertTrue(np.all(F[:,7]==0))
        r=currency_risk(self.returns,self.ex,self.fx)
        self.assertAlmostEqual(sum(r["components_pp"].values()),r["annualized_vol_pct"])
        self.assertAlmostEqual(sum(x["total_pp"] for x in r["rows"]),r["annualized_vol_pct"])
        cash=next(x for x in r["rows"] if x["ticker"]==CASH)
        self.assertAlmostEqual(cash["total_pp"],0.)
        with self.assertRaises(Exception):currency_parts(self.returns.drop(self.returns.index[10]),self.ex,self.fx)
    def test_pnl_unknown_preserved(self):
        p={"start":"2025-01-01","end":"2025-02-01","actual_pnl_twd":100.,"price_twd":30.,"fx_twd":20.,
            "interaction_twd":5.,"execution_vs_close_twd":-5.,"unallocated_pnl_twd":10.,
            "explicit_other_cashflow_twd":0.,"unexplained_twd":40.,"rows":[],"partial_decomposition":["A"],"missing":[]}
        r=recorded_currency_pnl({"1M":p})["windows"]["1M"]
        self.assertEqual(r["status"],"PARTIAL_RESEARCH_ONLY")
        self.assertEqual(r["known_fx_including_interaction_twd"],25.)
        self.assertEqual(r["identity_error_twd"],0.)
        self.assertEqual(recorded_currency_pnl({"1M":{**p,"actual_pnl_twd":101.}})["windows"]["1M"]["status"],"UNAVAILABLE")
    def test_rebalance_constraints_and_cost(self):
        r=rebalance_report(self.ex,self.returns,self.scenarios,self.cfg,self.opt)
        self.assertEqual(r["status"],"RESEARCH_ONLY",r)
        self.assertIn("minimum_volatility",r["candidates"])
        self.assertIn("risk_budget",r["candidates"])
        cols=list(self.returns.columns);A,b,bounds,_=constraint_matrix(cols,{h["ticker"]:h["bucket"] for h in self.ex["holdings"]},POLICY)
        self.assertLessEqual(r["candidates"]["minimum_volatility"]["annualized_vol_pct"],r["baseline"]["annualized_vol_pct"]+1e-6)
        self.assertLessEqual(r["candidates"]["risk_budget"]["risk_budget_rmse_pp"],r["baseline"]["risk_budget_rmse_pp"]+1e-5)
        for c in r["candidates"].values():
            w=np.array([s["after_pct"]/100 for s in c["weights"]])
            self.assertTrue(feasibility(w,A,b,bounds))
            self.assertLessEqual(c["nominal_turnover_pct"],15.+1e-5)
            self.assertAlmostEqual(sum(x["modeled_value_change_twd"] for x in c["weights"]),-c["estimated_cost_twd"],places=5)
            self.assertAlmostEqual(sum(g["risk_share_pct"] for g in c["groups"]),100.)
            self.assertAlmostEqual(c["stress"][0]["net_return_pct"],((1-c["estimated_cost_pct"]/100)*(1-.1*c["usd_quote_weight_pct"]/100)-1)*100)
            self.assertGreaterEqual(c["estimated_cost_twd"],0.)
    def test_no_relaxation_or_stale_exposure(self):
        e={**self.ex,"later_ledger_events":1}
        self.assertEqual(rebalance_report(e,self.returns,self.scenarios)["reason"],"EXPOSURE_QUALITY_GATE")
        r=rebalance_report(self.ex,self.returns.iloc[-26:],self.scenarios)
        self.assertEqual(r["status"],"INSUFFICIENT_SAMPLE")
        opt={**self.opt,"turnover_cap_pct":0}
        # Move 5% of cash into crypto, violating policy.
        e={**self.ex,"holdings":[dict(h) for h in self.ex["holdings"]]}
        e["holdings"][4]["weight"]+=.05;e["holdings"][6]["weight"]-=.05
        e["holdings"][4]["market_value_twd"]+=5000;e["holdings"][6]["market_value_twd"]-=5000
        r=rebalance_report(e,self.returns,self.scenarios,self.cfg,opt)
        self.assertEqual(r["status"],"INFEASIBLE")
        self.assertFalse(r["candidates"])
        self.assertTrue(r["current_policy_violations"])
if __name__=="__main__":unittest.main()
