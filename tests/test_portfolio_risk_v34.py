import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from performance_portfolio_risk import (CASH,BUCKETS,RiskBlocked,exposure,weekly_marks,risk_contributions,
    hypothetical,historical,event_replay,build_portfolio_risk)

class PortfolioRiskTests(unittest.TestCase):
    def setUp(self):
        self.end=pd.Timestamp("2026-11-25")
        self.d=self.end+pd.Timedelta(days=1)
        self.dates=pd.date_range(self.end-pd.Timedelta(weeks=60),self.end,freq="7D")
        self.fx=pd.Series(32.,index=self.dates)
        price=pd.Series(100.,index=self.dates)
        # Exact crypto dates avoid dependency on exchange holidays for synthetic test.
        self.market={"assets":{"BTC":{"price":price,"splits":[],"split_ratios":{},"bucket":"crypto","currency":"USD",
            "foreign":True,"instrument_id":"BTC-USD","source":"fixture","calendar":None}},"fx":self.fx,"quarantined":{}}
        self.tx=[{"date":self.dates[0],"qty":0.,"flow":10000.,"type":"deposit","ticker":""},
                 {"date":self.dates[0],"qty":1.,"flow":-3200.,"type":"buy","ticker":"BTC","category":"加密貨幣"}]
        self.nav={self.d-pd.Timedelta(days=7):10000.,self.d:10100.}
        self.cats={"BTC":"加密貨幣"}
    def exp(self):
        return exposure(self.nav,self.tx,self.cats,self.market,{},today=self.d)
    def test_exposure_no_gap_cash_and_frozen_cutoff(self):
        e=self.exp()
        self.assertEqual(e["basis"],"RECONSTRUCTED_LEDGER")
        self.assertEqual(e["model_nav_twd"],10000.)
        self.assertEqual(e["nav_gap_twd"],100.)
        self.assertEqual(next(x for x in e["holdings"] if x["ticker"]==CASH)["market_value_twd"],6800.)
        self.market["assets"]["BTC"]["price"].loc[self.d]=200.
        self.assertEqual(self.exp()["model_nav_twd"],10000.)
        s={"capture_mode":"automated_completed_daily_marks","quote_dates_verified":True,"fallback_count":0,
            "cash_twd":6800.,"holdings":{"BTC":{"shares":1.,"currency":"USD","instrument_id":"BTC-USD","market_value_twd":3300.}}}
        got=exposure(self.nav,self.tx,self.cats,self.market,{str(self.d.date()):s},today=self.d)
        self.assertEqual(got["basis"],"VALID_AUTOMATED_CAPTURE")
        self.assertEqual(got["model_nav_twd"],10100.)
    def test_active_missing_and_same_day_fail_closed(self):
        self.market["quarantined"]={"BTC":"fixture"}
        with self.assertRaises(RiskBlocked):self.exp()
        self.market["quarantined"]={}
        self.tx.append({"date":self.d,"qty":0.,"flow":1.,"type":"deposit","ticker":""})
        with self.assertRaises(RiskBlocked):self.exp()
    def test_missing_week_cannot_bridge(self):
        e=self.exp()
        p=self.market["assets"]["BTC"]["price"]
        self.market["assets"]["BTC"]["price"]=p.drop(self.dates[-4])
        f,r,latest,issues=weekly_marks(e,self.market,10)
        self.assertIn(str(self.dates[-4].date()),issues)
        self.assertEqual(len(latest),2)
        self.assertTrue(pd.isna(r.loc[self.dates[-4],"BTC"]))
        self.assertTrue(pd.isna(r.loc[self.dates[-3],"BTC"]))
        self.assertEqual(historical(e,f,4)["candidate_windows"],3)
    def test_euler_and_expected_shortfall_identity(self):
        e=self.exp();rng=np.random.default_rng(7)
        x=pd.DataFrame({"BTC":rng.normal(0,.04,52),CASH:np.zeros(52)},index=self.dates[-52:])
        r=risk_contributions(x,e)
        self.assertAlmostEqual(sum(s["risk_share_pct"] for s in r["rows"]),100.)
        self.assertAlmostEqual(sum(s["component_ann_vol_pp"] for s in r["rows"]),r["annualized_vol_pct"])
        self.assertAlmostEqual(sum(s["es95_component_loss_pp"] for s in r["rows"]),r["tail"]["es95_loss_pct"])
        self.assertAlmostEqual(r["tail"]["effective_tail_observations"],2.6)
        self.assertAlmostEqual(r["annualized_vol_pct"],x["BTC"].std()*np.sqrt(52)*.32*100)
        self.assertIsNone(risk_contributions(x.iloc[-26:],e)["tail"])
    def test_signed_hedge_and_funded_marginal(self):
        e={"holdings":[{"ticker":"A","bucket":"gold","weight":.2},{"ticker":"B","bucket":"global_equity","weight":.8}]}
        x=np.linspace(-.03,.03,52);r=pd.DataFrame({"A":-x,"B":x},index=self.dates[-52:])
        got=risk_contributions(r,e)
        self.assertLess(next(s for s in got["rows"] if s["ticker"]=="A")["risk_share_pct"],0.)
        self.assertAlmostEqual(sum(s["risk_share_pct"] for s in got["rows"]),100.)
    def test_multiplicative_fx_and_cash_stability(self):
        e=self.exp()
        s={"id":"fixture","label":"fixture","local_price_shocks":dict.fromkeys(BUCKETS,0.),"usd_twd_shock":.10}
        s["local_price_shocks"]["crypto"]=-.50
        s["local_price_shocks"]["cash"]=-.20
        r=hypothetical(e,s)
        self.assertAlmostEqual(r["return_pct"],.32*((1-.5)*(1+.1)-1)*100)
        self.assertAlmostEqual(r["pnl_twd"],-1440.)
        self.assertEqual(next(x for x in r["rows"] if x["ticker"]==CASH)["pnl_twd"],0.)
        self.assertAlmostEqual(sum(x["contribution_pp"] for x in r["rows"]),r["return_pct"])
    def test_scenarios_survive_insufficient_history(self):
        e=self.exp()
        c={"history_weeks":2,"scenarios":[{"id":"s","label":"s","local_price_shocks":dict.fromkeys(BUCKETS,0.),"usd_twd_shock":-.1}],
           "events":[{"id":"old","label":"old","start":"2020-01-01","end":"2020-02-01"}]}
        r=build_portfolio_risk(self.nav,self.tx,self.cats,self.market,{},c,today=self.d)
        self.assertEqual(r["status"],"PARTIAL_RESEARCH_ONLY")
        self.assertEqual(r["risk_windows"]["26"]["status"],"INSUFFICIENT_SAMPLE")
        self.assertEqual(r["hypothetical"][0]["status"],"HYPOTHETICAL")
        self.assertEqual(r["events"][0]["status"],"UNAVAILABLE")
        self.assertFalse(r["execution_permission"])

if __name__=="__main__":unittest.main()
