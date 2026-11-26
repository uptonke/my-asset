import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_constrained_optimizer import (POLICY, constraint_matrix, feasibility,
                                       solve_constrained, hrp_lite_weights, build_phase2_portfolios)


class Phase2Tests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(42)
        self.tickers = ["BOXX", "GLDM", "BTC-USD", "00981A", "QQQ", "VOO", "IFRA", "VEA"]
        self.buckets = dict(zip(self.tickers, ["cash","gold","crypto","taiwan_equity",
                                              "global_equity","global_equity","global_equity","global_equity"]))
        self.returns = pd.DataFrame(rng.normal(0, [.0001,.008,.04,.02,.015,.012,.014,.013], (200,8)),
                                    columns=self.tickers, index=pd.bdate_range("2025-01-01", periods=200))

    def test_solvers_respect_policy_and_cannot_overweight_cash(self):
        A,b,bounds,_ = constraint_matrix(self.tickers, self.buckets)
        for kind in ("variance","cvar"):
            with self.subTest(kind=kind):
                w,info = solve_constrained(self.returns,self.buckets,kind)
                self.assertEqual(info["status"],"OK")
                self.assertTrue(feasibility(w,A,b,bounds))
                self.assertLessEqual(w["BOXX"],.2000001)
                self.assertGreaterEqual(w["BOXX"],.0799999)
                self.assertGreaterEqual(w["GLDM"],.0299999)
                self.assertLessEqual(w["GLDM"],.0700001)
                self.assertLessEqual(w["IFRA"],.1000001)

    def test_infeasible_no_cash_or_gold(self):
        for drop in ("BOXX","GLDM"):
            df = self.returns.drop(columns=drop)
            buckets = {t:self.buckets[t] for t in df.columns}
            for kind in ("variance","cvar"):
                w,info = solve_constrained(df,buckets,kind)
                self.assertIsNone(w)
                self.assertEqual(info["status"],"INFEASIBLE")

    def test_common_hrp_and_metrics(self):
        current = pd.Series(1/8,index=self.tickers)
        w,info = hrp_lite_weights(self.returns)
        self.assertAlmostEqual(w.sum(),1.)
        self.assertGreaterEqual(w.min(),0.)
        self.assertIsNotNone(info["ewma_vol_pct"])
        out = build_phase2_portfolios(self.returns,current,{"snapshot_id":"test","asset_buckets":self.buckets,"skipped":[]})
        self.assertFalse(out["execution_permission"])
        for p in out["portfolios"].values():
            self.assertEqual(p["status"],"OK")
            self.assertEqual(p["metrics"]["sample_count"],200)
            self.assertEqual(len(p["weights"]),8)
            self.assertIsNotNone(p["metrics"]["es95_pct"])
            self.assertIsNotNone(p["metrics"]["max_drawdown_pct"])
            self.assertTrue(p["diagnostic_only"])

    def test_incomplete_universe_blocks_constrained(self):
        out=build_phase2_portfolios(self.returns,pd.Series(1/8,index=self.tickers),
            {"snapshot_id":"test","asset_buckets":self.buckets,"skipped":[{"ticker":"X"}]})
        self.assertEqual(out["portfolios"]["constrained_min_variance"]["status"],"INCOMPLETE_UNIVERSE")
        self.assertEqual(out["portfolios"]["constrained_cvar95"]["status"],"INCOMPLETE_UNIVERSE")


if __name__ == "__main__":
    unittest.main()
