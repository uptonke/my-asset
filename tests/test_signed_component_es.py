import ast
import math
import unittest
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATIONS = (ROOT / "scripts/update_stock_meta.py", ROOT / "update_stock_meta.py")


def load_function(path):
    # Extract pure function; no network calls or credentials.
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                and n.name == "historical_component_tail_risk")
    env = dict(pd=pd, np=np, math=math, Dict=Dict, Any=Any)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), env)
    return env[node.name]


class SignedComponentESTests(unittest.TestCase):
    def test_hedge_and_reconciliation(self):
        df = pd.DataFrame({"RISK": [-.04]*10 + [.01]*190, "HEDGE": [.02]*10 + [0.]*190})
        for path in IMPLEMENTATIONS:
            for alpha in (.95, .99):
                with self.subTest(path=path, alpha=alpha):
                    result = load_function(path)(df, {"RISK": .75, "HEDGE": .25}, {}, alpha)
                    rows = {r["ticker"]: r for r in result["rows"]}
                    self.assertEqual(result["status"], "OK")
                    self.assertAlmostEqual(result["net_signed_es_pct"], 2.5)
                    self.assertAlmostEqual(result["gross_tail_loss_pct"], 3.)
                    self.assertAlmostEqual(result["hedge_offset_pct"], -.5)
                    self.assertAlmostEqual(rows["HEDGE"]["component_es_pct"], -.5)
                    self.assertAlmostEqual(rows["HEDGE"]["component_es_share_pct"], -20.)
                    self.assertAlmostEqual(rows["RISK"]["component_es_share_pct"], 120.)
                    self.assertAlmostEqual(sum(r["component_es_share_pct"] for r in rows.values()), 100.)
                    self.assertAlmostEqual(result["top3_component_es_share_pct"], 120.)
                    self.assertAlmostEqual(result["top3_gross_tail_loss_share_pct"], 100.)
                    self.assertAlmostEqual(result["tail_concentration_hhi"], 1.)
                    self.assertLess(rows["HEDGE"]["half_cut_es_improvement_pct"], 0)
                    self.assertTrue(result["es_reconciliation_ok"])
                    self.assertTrue(result["var_reconciliation_ok"])
                    self.assertAlmostEqual(result["es_reconciliation_error_pct"], 0.)

    def test_nonpositive_net_es(self):
        df = pd.DataFrame({"A": [.01]*100, "B": [.02]*100})
        for path in IMPLEMENTATIONS:
            with self.subTest(path=path):
                result = load_function(path)(df, {"A": .5, "B": .5}, {})
                self.assertEqual(result["status"], "OK")
                self.assertEqual(result["es_pct"], 0.)
                self.assertAlmostEqual(result["net_signed_es_pct"], -1.5)
                self.assertIsNone(result["top3_component_es_share_pct"])
                self.assertIsNone(result["tail_concentration_hhi"])
                self.assertTrue(all(r["component_es_share_pct"] is None for r in result["rows"]))
                self.assertTrue(result["es_reconciliation_ok"])

    def test_all_assets_retained(self):
        df = pd.DataFrame({f"A{i}": [-.02-i*.001]*10 + [.005]*190 for i in range(13)})
        df["HEDGE"] = [.03]*10 + [0.]*190
        for path in IMPLEMENTATIONS:
            with self.subTest(path=path):
                result = load_function(path)(df, {c: 1. for c in df.columns}, {})
                self.assertEqual(len(result["rows"]), 14)
                self.assertEqual(result["rows"][-1]["ticker"], "HEDGE")
                self.assertTrue(result["es_reconciliation_ok"])
                self.assertAlmostEqual(sum(r["component_es_pct"] for r in result["rows"]), result["net_signed_es_pct"], delta=.008)

    def test_no_hedge(self):
        df = pd.DataFrame({"A": [-.03]*10 + [.01]*190, "B": [-.01]*10 + [.01]*190})
        for path in IMPLEMENTATIONS:
            with self.subTest(path=path):
                result = load_function(path)(df, {"A": .5, "B": .5}, {})
                self.assertAlmostEqual(result["net_signed_es_pct"], 2.)
                self.assertEqual(result["hedge_offset_pct"], 0.)
                self.assertAlmostEqual(result["rows"][0]["component_es_share_pct"], 75.)
                self.assertAlmostEqual(result["tail_concentration_hhi"], .625)


if __name__ == "__main__":
    unittest.main()
