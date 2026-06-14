# v6.0 Alpha Validation Gate

- Generated: `2026-06-14T16:41:27+00:00`
- Validation status: **watch_only_validation**
- Gates: `6` pass / `1` watch / `0` fail
- Further research rankings: `2`
- Trade signal enabled: `False`

## Gates
- `g1_feature_coverage` Feature coverage: **pass** — ok
- `g2_alpha_research_exists` Alpha research rows exist: **pass** — ok
- `g3_rebalance_ranking_exists` Rebalance ranking exists: **pass** — ok
- `g4_walk_forward_sample` Walk-forward validation depth: **pass** — ok
- `g5_model_governance` Model governance verdict: **watch** — governance_not_full_pass
- `g6_safety_flags` Safety flags remain disabled: **pass** — ok
- `g7_candidate_availability` Research candidate availability: **pass** — ok

## Safety boundary
- v6 pass/watch labels are validation labels only, not trade instructions.
- This output does not approve buy/sell, max Sharpe, or official rebalance.
