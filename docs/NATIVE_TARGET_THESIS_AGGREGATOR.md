# v10.5.3 Target Weight Origin Thesis Aggregator

Purpose: explain **where each target weight comes from**, not why a trade ticket was emitted.

For each asset this layer reports:

- current weight
- cloud target from `stock_meta[ticker].target_weight`
- v10.5 native target from the Optimizer Lab native engine
- 50/50 dual-source blend before conflict scaling
- conflict scaling / drift reduction when cloud% and v10.5% diverge
- final suggested target
- target-origin thesis in Chinese, for example: why a target implies add / trim / hold.

This layer reads previous outputs only. It does not recalculate weights, create orders, enable execution, or write Supabase.
