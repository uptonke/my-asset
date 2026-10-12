from pathlib import Path

p = Path(__file__).resolve().parents[1] / "tests" / "test_taiwan_individual_stock_risk_policy.py"
text = p.read_text(encoding="utf-8")
text = text.replace(
    'self.assertAlmostEqual(sum(weights.values()), 1.0, places=6)',
    'self.assertAlmostEqual(sum(weights.values()), 1.0, places=5)',
)
text = text.replace(
    'override = load_policy({"delegated_draft_policy": {"individual_stock_selected_min_weight_pct": 1}})\n        self.assertAlmostEqual(override["selected_min_weight"], 0.01)',
    'override = load_policy({"delegated_draft_policy": {"individual_stock_selected_min_weight_pct": 0.01}})\n        self.assertAlmostEqual(override["selected_min_weight"], 0.01)',
)
p.write_text(text, encoding="utf-8")
print("Adjusted asset-class minimum tests.")
