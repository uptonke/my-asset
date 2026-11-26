import json
import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from cost_walk_forward import trade_cost,simulate,CONFIG,OPT

class CostWalkForwardTests(unittest.TestCase):
    def test_self_financing(self):
        before=np.array([.6,.4]);target=np.array([.4,.6]);rates=np.array([.001,.002])
        c,turn=trade_cost(before,target,rates)
        self.assertAlmostEqual(c,float(rates@np.abs((1-c)*target-before)),places=12)
        self.assertAlmostEqual(((1-c)*target-before).sum(),-c,places=12)
        self.assertAlmostEqual(trade_cost(before,before,rates)[0],0.,places=12)
    def test_walk_forward(self):
        config=json.loads(CONFIG.read_text());opt=json.loads(OPT.read_text())
        config.update(training_observations=60,holding_observations=10)
        cols=[x["ticker"] for x in config["universe"]]
        rng=np.random.default_rng(4)
        prices=pd.DataFrame(100*np.cumprod(1+rng.normal(.0002,.01,(105,len(cols))),axis=0),columns=cols,index=pd.bdate_range("2024-01-01",periods=105))
        out=simulate(prices,config,opt,1.)
        self.assertGreaterEqual(len(out["folds"]),2)
        for m,a in out["aggregate"].items():
            self.assertLessEqual(a["net_return_pct"],a["gross_return_pct"]+1e-8)
            self.assertEqual(a["fold_count"],len(out["folds"]))
        self.assertAlmostEqual(out["aggregate"]["buy_hold"]["paid_cost_pct_initial_nav"],0.,places=10)
        for fold in out["folds"]:
            self.assertLess(fold["train_end"],fold["execution_date"])
            self.assertLess(fold["execution_date"],fold["test_start"])
        first=out["folds"][0];changed=prices.copy()
        changed.loc[first["test_start"]:,cols[0]]*=1.10
        other=simulate(changed,config,opt,1.)
        for m in first["methods"]:
            np.testing.assert_allclose(list(first["methods"][m]["target_weights"].values()),list(other["folds"][0]["methods"][m]["target_weights"].values()),atol=1e-9)
if __name__=="__main__":unittest.main()
