from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from taiwan_individual_stock_risk_policy import (  # noqa: E402
    classify_instrument,
    enforce_taiwan_individual_stock_policy,
    load_policy,
)


class TaiwanIndividualStockRiskPolicyTests(unittest.TestCase):
    def test_classifier_distinguishes_tw_etf_and_common_stock(self) -> None:
        self.assertEqual(classify_instrument({"ticker": "00981A", "asset_kind": "taiwan"}), "tw_etf")
        self.assertEqual(classify_instrument({"ticker": "2382", "asset_kind": "taiwan"}), "tw_individual_stock")
        self.assertEqual(classify_instrument({"ticker": "VOO", "asset_kind": "us"}), "other")

    def test_direct_stock_caps_include_etf_lookthrough(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            holdings_dir = root / "data" / "holdings" / "latest"
            holdings_dir.mkdir(parents=True)
            (holdings_dir / "00981A.json").write_text(
                json.dumps({
                    "holdings": [
                        {"ticker": "2382", "asset_class": "equity", "country": "Taiwan", "weight": 0.12}
                    ]
                }),
                encoding="utf-8",
            )
            rows = [
                {"ticker": "00981A", "asset_kind": "taiwan", "category": "台股"},
                {"ticker": "2382", "asset_kind": "taiwan", "category": "台股"},
                {"ticker": "2317", "asset_kind": "taiwan", "category": "台股"},
                {"ticker": "VOO", "asset_kind": "us", "category": "美股"},
                {"ticker": "QQQ", "asset_kind": "us", "category": "美股"},
            ]
            guarded, diagnostics, _ = enforce_taiwan_individual_stock_policy(
                root=root,
                weights={"00981A": 0.15, "2382": 0.20, "2317": 0.20, "VOO": 0.25, "QQQ": 0.20},
                asset_rows=rows,
                investable=1.0,
                min_weight=0.02,
                global_max_weight=0.40,
                policy=load_policy({}),
            )

            self.assertAlmostEqual(sum(guarded.values()), 1.0, places=7)
            self.assertLessEqual(guarded["2317"], 0.08 + 1e-8)
            self.assertLessEqual(guarded["2382"] + guarded["2317"], 0.15 + 1e-8)
            self.assertLessEqual(diagnostics["final_issuer_exposure_pct"]["2382"], 10.00001)

    def test_no_direct_tw_stock_is_identity(self) -> None:
        weights = {"00981A": 0.20, "VOO": 0.80}
        rows = [
            {"ticker": "00981A", "asset_kind": "taiwan", "category": "台股"},
            {"ticker": "VOO", "asset_kind": "us", "category": "美股"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            guarded, _, warnings = enforce_taiwan_individual_stock_policy(
                root=Path(tmp),
                weights=weights,
                asset_rows=rows,
                investable=1.0,
                min_weight=0.02,
                global_max_weight=0.40,
                policy=load_policy({}),
            )
        self.assertEqual(guarded, weights)
        self.assertEqual(warnings, [])


if __name__ == "__main__":
    unittest.main()
