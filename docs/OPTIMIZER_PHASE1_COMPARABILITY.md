# Optimizer phase 1 — common comparison basis and funding

Run Optimizer Lab with `all_optimizer_outputs` to produce a common TWD daily return matrix and current invested-asset weights for skfolio, Riskfolio and robustness. Standalone runs use the same loader but may have different snapshot IDs. Legacy reports without a snapshot ID are not cross-ranked. HRP-lite remains informational until its metrics are calculated on the same matrix.

Fixed current weights remain a reference, excluded from the best stability rank. Missing risk measures remain unavailable.

Trade Buffer blocks incomplete/stale snapshots (over seven calendar days), mismatched live holdings or weight deviations over 0.5 percentage points per asset, invalid total weights, negative cash or purchases exceeding gross sales. Amounts use invested assets, not NAV including cash. Existing cash is reserved, excess sales become residual cash; this check is before fees and does not authorize trades.

Phase 1 does not change solver objectives, trade approval or Supabase write paths. Constrained solving, realistic costs and comparable HRP-lite metrics are later phases.