# Backend Script Split v4.4

This version registers backend module boundaries without changing runtime behavior.

## Decision

`update_stock_meta.py` and existing optimizer scripts remain runtime-authoritative until dedicated tests are added.

## Target modules

- `scripts/modules/data_fetch.py`
- `scripts/modules/beta.py`
- `scripts/modules/synthetic_risk.py`
- `scripts/modules/optimizer_outputs.py`
- `scripts/modules/stock_meta_schema.py`

## Guardrail

Do not change Supabase write semantics, official weight logic, or optimizer JSON contracts during module extraction.
