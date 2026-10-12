from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise SystemExit(f"Expected block not found in {path}: {old[:120]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# 1) Config: 0.5% starter minimum for individual stocks; other selected assets keep 2%.
p = ROOT / "config" / "manual_approval_override.json"
replace_once(
    p,
    '    "individual_stock_policy_enabled": true,\n',
    '    "individual_stock_policy_enabled": true,\n    "individual_stock_selected_min_weight_pct": 0.005,\n',
)

# 2) Generic individual-stock policy: load the starter minimum and support per-ticker minima in guard normalization.
p = ROOT / "scripts" / "individual_stock_risk_policy.py"
replace_once(
    p,
    'DEFAULT_US_ISSUER_LOOKTHROUGH_MAX_WEIGHT = 0.15\n',
    'DEFAULT_US_ISSUER_LOOKTHROUGH_MAX_WEIGHT = 0.15\nDEFAULT_INDIVIDUAL_STOCK_SELECTED_MIN_WEIGHT = 0.005\n',
)
replace_once(
    p,
    '    return {\n        "enabled": bool(enabled),\n        "markets": {\n',
    '    return {\n        "enabled": bool(enabled),\n        "selected_min_weight": _ratio(\n            delegated.get("individual_stock_selected_min_weight_pct"),\n            DEFAULT_INDIVIDUAL_STOCK_SELECTED_MIN_WEIGHT,\n        ),\n        "markets": {\n',
)
replace_once(
    p,
    'def _normalize_with_caps(\n    raw: Dict[str, float],\n    investable: float,\n    min_weight: float,\n    caps: Dict[str, float],\n) -> Tuple[Dict[str, float], List[str]]:\n',
    'def _normalize_with_caps(\n    raw: Dict[str, float],\n    investable: float,\n    min_weight: float,\n    caps: Dict[str, float],\n    min_weight_by_ticker: Dict[str, float] | None = None,\n) -> Tuple[Dict[str, float], List[str]]:\n',
)
replace_once(
    p,
    '    if min_weight > 0:\n        max_selected = max(1, int(math.floor(investable / min_weight)))\n        if len(selected) > max_selected:\n            selected = dict(sorted(selected.items(), key=lambda kv: kv[1], reverse=True)[:max_selected])\n            warnings.append("individual_stock_guard_pool_pruned_by_min_weight_capacity")\n\n    impossible = [k for k in selected if caps.get(k, 1.0) + 1e-12 < min_weight]\n',
    '    def minimum_for(ticker: str) -> float:\n        if isinstance(min_weight_by_ticker, dict) and ticker in min_weight_by_ticker:\n            return max(0.0, _num(min_weight_by_ticker.get(ticker), min_weight))\n        return max(0.0, min_weight)\n\n    # Mixed asset classes can have different selected-position floors. Prune only\n    # when the sum of those floors cannot fit inside investable weight.\n    pruned_for_capacity = False\n    while len(selected) > 1 and sum(minimum_for(k) for k in selected) > investable + 1e-12:\n        weakest = min(selected, key=lambda k: selected[k])\n        selected.pop(weakest, None)\n        pruned_for_capacity = True\n    if pruned_for_capacity:\n        warnings.append("individual_stock_guard_pool_pruned_by_min_weight_capacity")\n\n    impossible = [k for k in selected if caps.get(k, 1.0) + 1e-12 < minimum_for(k)]\n',
)
replace_once(
    p,
    '        low = [k for k, value in fixed.items() if 0 < value < min_weight - 1e-12]\n',
    '        low = [k for k, value in fixed.items() if 0 < value < minimum_for(k) - 1e-12]\n',
)
replace_once(
    p,
    '    policy: Dict[str, Any],\n) -> Tuple[Dict[str, float], Dict[str, Any], List[str]]:\n',
    '    policy: Dict[str, Any],\n    min_weight_by_ticker: Dict[str, float] | None = None,\n) -> Tuple[Dict[str, float], Dict[str, Any], List[str]]:\n',
)
replace_once(
    p,
    '        guarded, bound_warnings = _normalize_with_caps(guarded, investable, min_weight, caps)\n',
    '        guarded, bound_warnings = _normalize_with_caps(\n            guarded, investable, min_weight, caps, min_weight_by_ticker=min_weight_by_ticker\n        )\n',
)

# 3) Base target normalizer: support per-ticker floors while preserving the old scalar default.
p = ROOT / "scripts" / "build_delegated_target_weight_draft_generator.py"
replace_once(
    p,
    '    min_w: float,\n    max_w: float,\n) -> Tuple[Dict[str, float], List[Dict[str, Any]], Dict[str, Any], List[str]]:\n',
    '    min_w: float,\n    max_w: float,\n    min_weight_by_ticker: Dict[str, float] | None = None,\n) -> Tuple[Dict[str, float], List[Dict[str, Any]], Dict[str, Any], List[str]]:\n',
)
replace_once(
    p,
    '    native_weights, warnings = normalize_with_bounds(raw, investable_weight, min_w, max_w)\n',
    '    native_weights, warnings = normalize_with_bounds(\n        raw, investable_weight, min_w, max_w, min_weight_by_ticker=min_weight_by_ticker\n    )\n',
)
replace_once(
    p,
    '    native_weights: Dict[str, float],\n    min_w: float,\n    max_w: float,\n) -> Tuple[Dict[str, float], Dict[str, Dict[str, Any]], List[Dict[str, Any]], List[str]]:\n',
    '    native_weights: Dict[str, float],\n    min_w: float,\n    max_w: float,\n    min_weight_by_ticker: Dict[str, float] | None = None,\n) -> Tuple[Dict[str, float], Dict[str, Dict[str, Any]], List[Dict[str, Any]], List[str]]:\n',
)
replace_once(
    p,
    '    final_weights, bound_warnings = normalize_with_bounds(raw_blend, investable_weight, min_w, max_w)\n',
    '    final_weights, bound_warnings = normalize_with_bounds(\n        raw_blend, investable_weight, min_w, max_w, min_weight_by_ticker=min_weight_by_ticker\n    )\n',
)
old_normalize = '''def normalize_with_bounds(raw: Dict[str, float], investable: float, min_w: float, max_w: float) -> Tuple[Dict[str, float], List[str]]:\n    warnings: List[str] = []\n    if investable <= 0 or not raw:\n        return {}, ["no_investable_weight_or_empty_pool"]\n\n    # Keep positive raw weights only; min weight is applied only after an asset is selected.\n    selected = {k: max(0.0, v) for k, v in raw.items() if v > 1e-12}\n    if not selected:\n        return {}, ["no_positive_raw_scores"]\n\n    # If too many selected assets for the min weight, keep the strongest names.\n    max_selected_by_min = max(1, int(math.floor(investable / min_w))) if min_w > 0 else len(selected)\n    if len(selected) > max_selected_by_min:\n        selected = dict(sorted(selected.items(), key=lambda kv: kv[1], reverse=True)[:max_selected_by_min])\n        warnings.append("pool_pruned_by_min_weight_capacity")\n\n    # Initial normalization.\n    total = sum(selected.values()) or 1.0\n    weights = {k: investable * v / total for k, v in selected.items()}\n\n    # Drop names below min and renormalize until stable.\n    changed = True\n    while changed and weights:\n        changed = False\n        low = [k for k, v in weights.items() if v < min_w - 1e-12]\n        if low and len(weights) > 1:\n            for k in low:\n                weights.pop(k, None)\n            total = sum(weights.values()) or 1.0\n            weights = {k: investable * v / total for k, v in weights.items()}\n            changed = True\n            warnings.append("low_weight_assets_excluded")\n\n    # Cap high weights and redistribute residual among uncapped names.\n    capped: Dict[str, float] = {}\n    free = dict(weights)\n    remaining = investable\n    while free:\n        total_free = sum(free.values()) or 1.0\n        proposed = {k: remaining * v / total_free for k, v in free.items()}\n        newly_capped = {k: max_w for k, v in proposed.items() if v > max_w}\n        if not newly_capped:\n            capped.update(proposed)\n            break\n        capped.update(newly_capped)\n        for k in newly_capped:\n            free.pop(k, None)\n        remaining = investable - sum(capped.values())\n        if remaining <= 1e-12:\n            break\n        warnings.append("single_asset_cap_applied")\n\n    # Final tiny residual correction on largest nonzero row.\n    total_out = sum(capped.values())\n    if capped and abs(total_out - investable) > 1e-8:\n        k = max(capped, key=lambda x: capped[x])\n        capped[k] = max(0.0, min(max_w, capped[k] + (investable - total_out)))\n\n    return {k: round6(v) for k, v in capped.items() if v > 1e-8}, warnings\n'''
new_normalize = '''def normalize_with_bounds(\n    raw: Dict[str, float],\n    investable: float,\n    min_w: float,\n    max_w: float,\n    min_weight_by_ticker: Dict[str, float] | None = None,\n) -> Tuple[Dict[str, float], List[str]]:\n    warnings: List[str] = []\n    if investable <= 0 or not raw:\n        return {}, ["no_investable_weight_or_empty_pool"]\n\n    selected = {k: max(0.0, v) for k, v in raw.items() if v > 1e-12}\n    if not selected:\n        return {}, ["no_positive_raw_scores"]\n\n    def minimum_for(ticker: str) -> float:\n        if isinstance(min_weight_by_ticker, dict) and ticker in min_weight_by_ticker:\n            return max(0.0, num(min_weight_by_ticker.get(ticker), min_w))\n        return max(0.0, min_w)\n\n    # With mixed floors (e.g. 0.5% starter stocks vs 2% funds), capacity\n    # depends on the sum of each selected asset's own floor.\n    pruned_for_capacity = False\n    while len(selected) > 1 and sum(minimum_for(k) for k in selected) > investable + 1e-12:\n        weakest = min(selected, key=lambda k: selected[k])\n        selected.pop(weakest, None)\n        pruned_for_capacity = True\n    if pruned_for_capacity:\n        warnings.append("pool_pruned_by_min_weight_capacity")\n\n    total = sum(selected.values()) or 1.0\n    weights = {k: investable * v / total for k, v in selected.items()}\n\n    changed = True\n    while changed and weights:\n        changed = False\n        low = [k for k, v in weights.items() if v < minimum_for(k) - 1e-12]\n        if low and len(weights) > 1:\n            for k in low:\n                weights.pop(k, None)\n            total = sum(weights.values()) or 1.0\n            weights = {k: investable * v / total for k, v in weights.items()}\n            changed = True\n            warnings.append("low_weight_assets_excluded")\n\n    capped: Dict[str, float] = {}\n    free = dict(weights)\n    remaining = investable\n    while free:\n        total_free = sum(free.values()) or 1.0\n        proposed = {k: remaining * v / total_free for k, v in free.items()}\n        newly_capped = {k: max_w for k, v in proposed.items() if v > max_w}\n        if not newly_capped:\n            capped.update(proposed)\n            break\n        capped.update(newly_capped)\n        for k in newly_capped:\n            free.pop(k, None)\n        remaining = investable - sum(capped.values())\n        if remaining <= 1e-12:\n            break\n        warnings.append("single_asset_cap_applied")\n\n    total_out = sum(capped.values())\n    if capped and abs(total_out - investable) > 1e-8:\n        k = max(capped, key=lambda x: capped[x])\n        capped[k] = max(0.0, min(max_w, capped[k] + (investable - total_out)))\n\n    return {k: round6(v) for k, v in capped.items() if v > 1e-8}, warnings\n'''
replace_once(p, old_normalize, new_normalize)

# 4) Guarded wrapper: classify every asset and pass 0.5% only to direct stocks.
p = ROOT / "scripts" / "build_delegated_target_weight_draft_guarded.py"
replace_once(
    p,
    'LAST_WARNINGS: List[str] = []\n\n_ORIGINAL_NATIVE = base.build_v105_native_target_weights\n',
    'LAST_WARNINGS: List[str] = []\n\n\ndef _selected_min_weight_map(\n    asset_rows: List[Dict[str, Any]], default_min_weight: float\n) -> Dict[str, float]:\n    stock_min = max(0.0, float(STOCK_POLICY.get("selected_min_weight", 0.005)))\n    out: Dict[str, float] = {}\n    for row in asset_rows:\n        ticker = str(row.get("ticker") or row.get("symbol") or "").strip()\n        if not ticker:\n            continue\n        classification = classify_instrument(row, ROOT)\n        out[ticker] = stock_min if classification in {\n            "tw_individual_stock", "us_individual_stock"\n        } else default_min_weight\n    return out\n\n\n_ORIGINAL_NATIVE = base.build_v105_native_target_weights\n',
)
replace_once(
    p,
    '        global_max_weight=max_w,\n        policy=STOCK_POLICY,\n    )\n',
    '        global_max_weight=max_w,\n        policy=STOCK_POLICY,\n        min_weight_by_ticker=_selected_min_weight_map(asset_rows, min_w),\n    )\n',
)
replace_once(
    p,
    '        daily_quant_context,\n        min_w,\n        max_w,\n    )\n',
    '        daily_quant_context,\n        min_w,\n        max_w,\n        min_weight_by_ticker=_selected_min_weight_map(asset_rows, min_w),\n    )\n',
)
replace_once(
    p,
    '        native_weights,\n        min_w,\n        max_w,\n    )\n',
    '        native_weights,\n        min_w,\n        max_w,\n        min_weight_by_ticker=_selected_min_weight_map(asset_rows, min_w),\n    )\n',
)
replace_once(
    p,
    '    target_policy["individual_stock_policy_enabled"] = bool(STOCK_POLICY.get("enabled", True))\n\n    tw = _market_policy("taiwan")\n',
    '    target_policy["individual_stock_policy_enabled"] = bool(STOCK_POLICY.get("enabled", True))\n    target_policy["individual_stock_selected_min_weight_pct"] = round(\n        float(STOCK_POLICY.get("selected_min_weight", 0.005)) * 100, 6\n    )\n\n    tw = _market_policy("taiwan")\n',
)
replace_once(
    p,
    '    summary["individual_stock_policy_enabled"] = bool(STOCK_POLICY.get("enabled", True))\n',
    '    summary["individual_stock_policy_enabled"] = bool(STOCK_POLICY.get("enabled", True))\n    summary["individual_stock_selected_min_weight_pct"] = round(\n        float(STOCK_POLICY.get("selected_min_weight", 0.005)) * 100, 6\n    )\n',
)
replace_once(
    p,
    '            row["instrument_classification"] = classification\n            row["effective_max_weight_rule_pct"] = effective_caps.get(ticker, default_cap_pct)\n',
    '            row["instrument_classification"] = classification\n            row["effective_min_weight_rule_pct"] = round(\n                (float(STOCK_POLICY.get("selected_min_weight", 0.005))\n                 if classification in {"tw_individual_stock", "us_individual_stock"}\n                 else float(target_policy.get("included_asset_min_weight_pct", 0.02))) * 100,\n                6,\n            )\n            row["effective_max_weight_rule_pct"] = effective_caps.get(ticker, default_cap_pct)\n',
)
replace_once(
    p,
    '        "US: direct stock <= 10%, US direct-stock sleeve <= 25%, ETF look-through plus direct exposure to the same issuer <= 15% when feasible."\n',
    '        "US: direct stock <= 10%, US direct-stock sleeve <= 25%, ETF look-through plus direct exposure to the same issuer <= 15% when feasible. "\n        "Selected individual stocks may use a 0.5% starter-position minimum; other selected assets retain the 2% minimum."\n',
)

# 5) Tests: mixed floors keep ~1% stocks while excluding a 1% fund/ETF.
p = ROOT / "tests" / "test_taiwan_individual_stock_risk_policy.py"
replace_once(
    p,
    'from individual_stock_risk_policy import (  # noqa: E402\n',
    'from build_delegated_target_weight_draft_generator import normalize_with_bounds  # noqa: E402\nfrom individual_stock_risk_policy import (  # noqa: E402\n',
)
insert_before = '\n\nif __name__ == "__main__":\n    unittest.main()\n'
new_tests = '''\n    def test_mixed_minimum_keeps_starter_stocks_but_drops_small_fund(self) -> None:\n        raw = {\n            "2382": 0.011,\n            "2317": 0.009,\n            "VEA": 0.010,\n            "VOO": 0.323,\n            "QQQ": 0.323,\n            "BOXX": 0.324,\n        }\n        minima = {\n            "2382": 0.005,\n            "2317": 0.005,\n            "VEA": 0.02,\n            "VOO": 0.02,\n            "QQQ": 0.02,\n            "BOXX": 0.02,\n        }\n        weights, _ = normalize_with_bounds(\n            raw, investable=1.0, min_w=0.02, max_w=0.40, min_weight_by_ticker=minima\n        )\n        self.assertIn("2382", weights)\n        self.assertIn("2317", weights)\n        self.assertNotIn("VEA", weights)\n        self.assertGreaterEqual(weights["2382"], 0.005)\n        self.assertGreaterEqual(weights["2317"], 0.005)\n        self.assertAlmostEqual(sum(weights.values()), 1.0, places=6)\n\n    def test_guard_respects_per_ticker_starter_minimum(self) -> None:\n        rows = [\n            {"ticker": "2382", "asset_kind": "taiwan", "category": "台股"},\n            {"ticker": "2317", "asset_kind": "taiwan", "category": "台股"},\n            {"ticker": "VEA", "asset_kind": "us", "category": "美股"},\n            {"ticker": "VOO", "asset_kind": "us", "category": "美股"},\n            {"ticker": "QQQ", "asset_kind": "us", "category": "美股"},\n            {"ticker": "BOXX", "asset_kind": "us", "category": "美股"},\n        ]\n        minima = {\n            "2382": 0.005, "2317": 0.005, "VEA": 0.02,\n            "VOO": 0.02, "QQQ": 0.02, "BOXX": 0.02,\n        }\n        with tempfile.TemporaryDirectory() as tmp:\n            guarded, _, _ = enforce_individual_stock_policy(\n                root=Path(tmp),\n                weights={"2382": 0.011, "2317": 0.009, "VEA": 0.010, "VOO": 0.323, "QQQ": 0.323, "BOXX": 0.324},\n                asset_rows=rows,\n                investable=1.0,\n                min_weight=0.02,\n                global_max_weight=0.40,\n                policy=load_policy({}),\n                min_weight_by_ticker=minima,\n            )\n        self.assertIn("2382", guarded)\n        self.assertIn("2317", guarded)\n        self.assertNotIn("VEA", guarded)\n        self.assertGreaterEqual(guarded["2382"], 0.005)\n        self.assertGreaterEqual(guarded["2317"], 0.005)\n\n    def test_policy_exposes_individual_stock_starter_minimum(self) -> None:\n        default_policy = load_policy({})\n        self.assertAlmostEqual(default_policy["selected_min_weight"], 0.005)\n        override = load_policy({"delegated_draft_policy": {"individual_stock_selected_min_weight_pct": 1}})\n        self.assertAlmostEqual(override["selected_min_weight"], 0.01)\n'''
text = p.read_text(encoding="utf-8")
if 'test_mixed_minimum_keeps_starter_stocks_but_drops_small_fund' not in text:
    if insert_before not in text:
        raise SystemExit('test insertion marker missing')
    text = text.replace(insert_before, '\n' + new_tests + insert_before, 1)
    p.write_text(text, encoding="utf-8")

print("Asset-class minimum-weight patch applied.")
