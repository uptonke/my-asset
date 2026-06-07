# Backend Module Registry v4.4

- Status: **OK**
- Module count: `5`
- Runtime refactor enabled: `False`

## Modules
- `data_fetch` — exists: `True` — concerns: market data retrieval, raw price input, ticker metadata input
- `beta` — exists: `True` — concerns: beta, rolling correlation, market exposure diagnostics
- `synthetic_risk` — exists: `True` — concerns: synthetic risk scores, risk flags, risk bucket mapping
- `optimizer_outputs` — exists: `True` — concerns: optimizer JSON output, safe-mode flags, decision support artifacts
- `stock_meta_schema` — exists: `True` — concerns: stock_meta contract, schema compatibility, frontend field stability

## Policy
- This version registers backend boundaries only.
- update_stock_meta.py remains authoritative until module tests are added.
