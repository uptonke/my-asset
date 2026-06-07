# Schema Registry v4.5

This repository uses `schemas/schema_registry.json` as the lightweight source of truth for JSON output contracts.

## Scope

The registry covers:

- `data/optimizer/*_latest.json`
- `data/repo_architecture/*_latest.json`

The validator is intentionally conservative and structural. It checks top-level contracts, required fields, and safety invariants, without overfitting every model-specific nested field.

## Safety invariants

The validation gate fails if optimizer outputs enable unsafe execution flags:

- `execution_permission: true`
- `official_alpha_enabled: true`
- `alpha_model_enabled: true`
- `maximum_sharpe_optimization_enabled: true`
- `auto_trade_enabled: true`
- `supabase_write_enabled: true`
- `not_trade_order: false`

## Commands

```bash
python scripts/validate_repo_integrity.py
npm run validate:repo
```

## Governance meaning

Passing v4.6 means the repo is structurally coherent. It does not mean any optimizer output is approved for trading or formal portfolio execution.
