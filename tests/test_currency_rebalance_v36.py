import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from performance_currency_rebalance import historical_fx,currency_risk,rebalancing,build_extensions,CASH
from performance_portfolio_risk import risk_contributions,hypothetical,BUCKETS
from run_constrained_optimizer import constraint_matrix,feasibility,POLICY

class CurrencyRebalanceTests(unittest.TestCase):
    def setUp(self):
        self.cols=["A","B","C","D","TW","BTC","GLD","BOXX",CASH]
        buckets=["global_equity"]*4+["taiwan_equity","crypto","gold","cash","cash"]
        w=[.15,.15,.13,.12,.14,.16,.05,.09,.01]
        self.ex={"model_nav_twd":100000.,"nav_gap_pct":0.,"later_ledger_events":0,
            "holdings":[{"ticker":t,"bucket":g,"currency":"TWD" if t in ("TW",CASH) else "USD",
                         "weight":v,"market_value_twd":v*100000} for t,g,v in zip(self.cols,buckets,w)]}
        self.dates=pd.date_range("2025-01-01",periods=53,freq="7D")
        rng=np.random.default_rng(73)
        f=rng.normal(0,.009,52)
        local=rng.normal(.001,.021,(52,len(w)));local[:,5]*=2;local[:,7]=0;local[:,-1]=0
        self.local=local
        usd=np.array([h["currency"]=="USD" for h in self.ex["holdings"]])
        self.returns=pd.DataFrame((1+local)*(1+f[:,None]*usd)-1,index=self.dates[1:],columns=self.cols)
        self.market={"fx":pd.Series(32*np.r_[1,np.cumprod(1+f)],index=self.dates)}
        self.s=[hypothetical(self.ex,{"id":"fx","label":"fx","local_price_shocks":dict.fromkeys(BUCKETS,0.),"usd_twd_shock":-.1})]
    def test_fx_euler_and_pure_translation(self):
        r=currency_risk(self.ex,self.market,self.returns)
        base=risk_contributions(self.returns,self.ex)
        self.assertAlmostEqual(r["annualized_vol_pct"],base["annualized_vol_pct"])
        self.assertAlmostEqual(sum(x["risk_share_pct"] for x in r["rows"]),100.)
        self.assertAlmostEqual(r["currency_neutral_ann_vol_pct"],np.std(self.local@np.array([h["weight"] for h in self.ex["holdings"]]),ddof=1)*np.sqrt(52)*100)
        self.assertAlmostEqual(r["usd_weight_pct"],85.)
        self.assertAlmostEqual(r["fx_only_1pct_pnl_twd"],850.)
        for x in r["assets"]:
            if x["currency"]=="TWD":self.assertAlmostEqual(x["fx_component_ann_vol_pp"],0.)
        self.assertAlmostEqual(sum(x["fx_component_ann_vol_pp"] for x in r["assets"]),r["rows"][1]["component_ann_vol_pp"])
    def test_fx_pnl_keeps_unknown_separate(self):
        p={"start":"2026-01-01","end":"2026-02-01","status":"PARTIAL","actual_pnl_twd":21.,"explicit_other_cashflow_twd":-1.,
            "unexplained_twd":5.,"missing":[{"ticker":"X"}],"rows":[
            {"ticker":"A","pnl_twd":10.,"price_twd":5.,"fx_twd":4.,"interaction_twd":2.,"execution_vs_close_twd":-1.},
            {"ticker":"B","pnl_twd":7.,"price_twd":None,"fx_twd":None,"interaction_twd":None,"execution_vs_close_twd":None}]}
        r=historical_fx({"SI":p})["windows"]["SI"]
        self.assertEqual(r["status"],"PARTIAL")
        self.assertEqual(r["fx_plus_interaction_twd"],6.)
        self.assertEqual(r["unallocated_asset_pnl_twd"],7.)
        self.assertIsNone(r["rows"][1]["fx_twd"])
        self.assertAlmostEqual(r["identity_error_twd"],0.)
    def test_rebalancing_constraints_and_net_stress(self):
        r=rebalancing(self.ex,self.returns,self.s)
        self.assertFalse(r["current_policy_feasible"])
        self.assertIn("crypto_max",r["current_policy_violations"])
        self.assertEqual(len(r["candidates"]),6)
        ok=[x for x in r["candidates"] if x["status"]=="RESEARCH_ONLY"]
        self.assertTrue(any(x["objective"]=="minimum_variance" for x in ok))
        self.assertTrue(any(x["objective"]=="risk_budget" for x in ok))
        A,b,bounds,_=constraint_matrix(self.cols,{h["ticker"]:h["bucket"] for h in self.ex["holdings"]},POLICY)
        for x in ok:
            w=np.array([t["target_pct"]/100 for t in x["trades"]])
            self.assertTrue(feasibility(w,A,b,bounds))
            self.assertLessEqual(x["nominal_turnover_pct"],x["turnover_cap_pct"]+1e-5)
            self.assertAlmostEqual(sum(t["signed_change_twd"] for t in x["trades"]),-x["estimated_cost_twd"],places=6)
            self.assertAlmostEqual(sum(g["risk_share_pct"] for g in x["groups"]),100.,places=8)
            self.assertLessEqual(x["stress"][0]["net_including_cost_pct"],x["stress"][0]["return_pct"]+1e-9)
            self.assertAlmostEqual(x["stress"][0]["return_pct"],-x["usd_weight_pct"]*.1)
        self.assertFalse(r["execution_permission"])
    def test_rebalancing_blocked_by_quality_or_sample(self):
        _,r=build_extensions({**self.ex,"nav_gap_pct":1.1},self.market,self.returns,self.s)
        self.assertEqual(r["status"],"BLOCKED")
        _,r=build_extensions(self.ex,self.market,self.returns.iloc[-26:],self.s)
        self.assertEqual(r["status"],"INSUFFICIENT_SAMPLE")
    def test_missing_fx_not_zero(self):
        with self.assertRaises(Exception):currency_risk(self.ex,{"fx":pd.Series(dtype=float)},self.returns)
if __name__=="__main__":unittest.main()
