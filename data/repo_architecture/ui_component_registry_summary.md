# UI Component Split Registry v4.3

- Status: **OK**
- Component count: `4`
- Runtime split enabled: `False`
- Source of truth: `assets/js/src/app.bundle.source.js`

## Components
- `quant-risk` — 量化風控 — `registry_first_not_runtime_split` — module exists: `True`
- `optimizer-lab` — 最佳化 — `registry_first_not_runtime_split` — module exists: `True`
- `macro-intelligence` — 市場環境 — `anchor_stabilized_not_runtime_split` — module exists: `True`
- `holding-cards` — 持倉卡片 — `registry_first_not_runtime_split` — module exists: `True`

## Policy
- This is a registry-first split. It does not change runtime behavior.
- Actual extraction should happen only after build and validation gates remain green.
