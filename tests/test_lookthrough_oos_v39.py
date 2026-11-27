import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from performance_lookthrough import combined_exposure, issuer_concentration
from performance_oos_risk_budget import validate_oos,METHODS

def h(t,w,b="global_equity",c="USD"):
    return {"ticker":t,"weight":w,"market_value_twd":100*w,"bucket":b,"currency":c}
def stock(t,w,ident="",kind="ISIN",country=None,sector=None,exchange=None):
    return {"ticker":t,"weight":w,"id":ident,"id_type":kind,"asset_class":"equity",
            "country":country,"sector":sector,"exchange":exchange}
def snap(f,rows,d="2026-11-25",quality="OFFICIAL_DAILY"):
    return {"fund":f,"as_of":d,"source_quality":quality,"lookthrough_mode":"EQUITY_LOOKTHROUGH","holdings":rows}

class IssuerTests(unittest.TestCase):
    def test_explicit_merge_and_proxy(self):
        rows=[{"key":"ISIN:US02079K3059","name":"Alphabet A","ticker":"GOOGL","direct_pct":3.,"indirect_pct":0.,"total_pct":3.,"source_funds":[]},
              {"key":"CUSIP:02079K107","name":"Alphabet C","ticker":"GOOG","direct_pct":0.,"indirect_pct":4.,"total_pct":4.,"source_funds":["VOO"]},
              {"key":"US:OTHER","name":"Other","ticker":"OTHER","direct_pct":5.,"indirect_pct":0.,"total_pct":5.,"source_funds":[]}]
        r=issuer_concentration(rows)
        self.assertAlmostEqual(r["hhi"],10000*((7/12)**2+(5/12)**2))
        self.assertAlmostEqual(r["confirmed_mapping_pct"],100*7/12)
        self.assertAlmostEqual(r["rows"][0]["total_pct"],7)
        self.assertEqual(r["rows"][0]["source_funds"],["VOO"])
        self.assertEqual(r["status"],"PARTIAL_RESEARCH_ONLY")
        self.assertIsNone(issuer_concentration([])["hhi"])

class LookthroughTests(unittest.TestCase):
    def setUp(self):
        self.ex={"as_of":"2026-11-26","basis":"RECONSTRUCTED_LEDGER",
            "holdings":[h("VOO",.4),h("QQQ",.2),h("NVDA",.1),h("UNKNOWN",.1),
                        h("__TWD_CASH__",.2,"cash","TWD")]}
        self.snap={"VOO":snap("VOO",[stock("NVDA",.1,"US67066G1040",country="UNITED STATES",sector="INFORMATION TECHNOLOGY"),
                                      stock("AAPL",.8,"US0378331005",country="United States",sector="Information Technology")]),
                   "QQQ":snap("QQQ",[stock("NVDA",.2,"67066G104","CUSIP"),
                                       stock("AAPL",.8,"037833100","CUSIP")])}
    def test_direct_cusip_isin_and_no_renormalization(self):
        r=combined_exposure(self.ex,self.snap)
        n=next(x for x in r["rows"] if x["ticker"]=="NVDA")
        self.assertAlmostEqual(n["direct_pct"],10)
        self.assertAlmostEqual(n["indirect_pct"],8)
        self.assertAlmostEqual(n["total_pct"],18)
        self.assertEqual(n["sector"],"Information Technology")
        self.assertEqual(n["country"],"United States")
        self.assertAlmostEqual(r["mapped_equity_pct"],66)
        self.assertAlmostEqual(r["unmapped_pct"],14)
        self.assertAlmostEqual(r["non_equity_pct"],20)
        self.assertAlmostEqual(r["mapped_equity_hhi"],10000*((18/66)**2+(48/66)**2))
        self.assertAlmostEqual(sum(x["portfolio_pct"] for x in r["sector"]),66)
        self.assertEqual(r["status"],"PARTIAL_RESEARCH_ONLY")
    def test_future_and_stale_snapshots(self):
        self.snap["VOO"]["as_of"]="2026-11-27"
        r=combined_exposure(self.ex,self.snap)
        self.assertAlmostEqual(r["mapped_equity_pct"],20)
        self.assertAlmostEqual(r["unmapped_pct"],60)
        self.snap["VOO"]["as_of"]="2026-07-31"
        r=combined_exposure(self.ex,self.snap)
        self.assertIn("STALE:VOO",r["warnings"])
    def test_invalid_weights_and_conflicting_country(self):
        self.snap["VOO"]["holdings"][0]["weight"]=.9
        r=combined_exposure(self.ex,self.snap)
        self.assertTrue(any(x["reason"]=="INVALID_EQUITY_WEIGHTS" for x in r["unmapped"]))
        self.snap["VOO"]["holdings"][0]["weight"]=.1
        self.snap["QQQ"]["holdings"][0]["country"]="Canada"
        r=combined_exposure(self.ex,self.snap)
        self.assertEqual(next(x for x in r["rows"] if x["ticker"]=="NVDA")["country"],"Unknown")

class OOSTests(unittest.TestCase):
    def setUp(self):
        self.hs=[h("A",.15),h("B",.15),h("C",.15),h("D",.15),h("TW",.1,"taiwan_equity","TWD"),
                 h("BTC",.1,"crypto"),h("GLD",.05,"gold"),h("BOXX",.1,"cash"),h("__TWD_CASH__",.05,"cash","TWD")]
        self.ex={"holdings":self.hs}
        rng=np.random.default_rng(91);x=rng.normal(.001,.012,(77,len(self.hs)));x[:,-1]=0
        self.r=pd.DataFrame(x,index=pd.date_range("2024-01-03",periods=77,freq="7D"),columns=[v["ticker"] for v in self.hs])
    def test_no_lookahead_and_same_dates(self):
        r=validate_oos(self.ex,self.r)
        self.assertEqual(r["status"],"RESEARCH_ONLY")
        self.assertEqual(r["fold_count"],5)
        self.assertEqual(r["evaluation_weeks"],25)
        self.assertEqual(set(r["aggregates"]),set(METHODS))
        f=r["folds"][0]
        self.assertLess(f["train_end"],f["execution_date"])
        self.assertLess(f["execution_date"],f["test_start"])
        other=self.r.copy();other.iloc[52:]*=1.7
        pd.testing.assert_frame_equal(self.r.iloc[:52],other.iloc[:52],check_exact=True)
        rr=validate_oos(self.ex,other)
        for m in METHODS:
            a=f["methods"][m]["signal_weights"]
            b=rr["folds"][0]["methods"][m]["signal_weights"]
            self.assertEqual(a is None,b is None)
            if a is not None:
                self.assertEqual(set(a),set(b))
                # SLSQP/BLAS roundoff is not lookahead: allow at most 0.0001 pp.
                np.testing.assert_allclose([a[t] for t in sorted(a)],[b[t] for t in sorted(a)],rtol=0,atol=1e-6)
            self.assertEqual(r["aggregates"][m]["observations"],25)
            self.assertLessEqual(r["aggregates"][m]["net_return_pct"],r["aggregates"][m]["gross_return_pct"]+1e-7)
            self.assertAlmostEqual(sum(x["risk_pct"] for x in r["aggregates"][m]["realized_gross_risk"]),100.)
        self.assertTrue(any(f["methods"]["minimum_variance"]["signal_weights"] is not None for f in r["folds"]))
    def test_initial_not_current_weights_and_gap(self):
        r=validate_oos(self.ex,self.r.iloc[:57])
        ex={"holdings":[{**x,"weight":0.} for x in self.hs]}
        rr=validate_oos(ex,self.r.iloc[:57])
        self.assertEqual(r["initial_weights"],rr["initial_weights"])
        self.assertEqual(validate_oos(self.ex,self.r.iloc[:56])["status"],"INSUFFICIENT_SAMPLE")
        with self.assertRaises(ValueError):validate_oos(self.ex,self.r.drop(self.r.index[10]))
if __name__=="__main__":unittest.main()
