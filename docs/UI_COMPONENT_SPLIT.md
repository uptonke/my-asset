# UI Component Split v4.3

This version establishes component ownership before moving executable UI code.

## Decision

- Authoritative frontend source remains `assets/js/src/app.bundle.source.js`.
- Runtime bundle remains `assets/js/app.bundle.js`.
- Component files under `assets/js/src/components/` are registry-first boundaries, not independently bundled runtime modules yet.

## Registered boundaries

- Quant Risk: risk metrics, VaR/ES, drawdown, risk contribution.
- Optimizer Lab: v1-v3 optimizer panels, decision support, approval, audit, governance.
- Macro Intelligence: market intelligence and macro context, anchored outside risk/optimizer duplicate panes.
- Holding Cards: position-level display and holding cards.

## Guardrail

Do not hand-edit `assets/js/app.bundle.js`. Change source first, then rebuild.
