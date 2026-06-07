# v1.9.1 Workflow Consolidation Map

- Timestamp UTC: `2026-06-07T03:56:03.078175+00:00`
- Consolidated workflow: `.github/workflows/optimizer-lab.yml`

## Kept production workflows

- `daily_update.yml`
- `update_stock_meta.yml`
- `weekly_backup.yml`
- `weekly_macro_update.yml`

## Deleted legacy optimizer workflows

- `apply_terminal_ia_phase2.yml.yml`
- `optimizer-install-sandbox.yml.yml`
- `optimizer-robustness.yml.yml`
- `optimizer-stress-tests.yml.yml`
- `riskfolio-dependency-sandbox.yml.yml`
- `riskfolio-sandbox.yml.yml`
- `skfolio-sandbox.yml.yml`

## Unknown workflows not deleted

- `optimizer-lab.yml.yml`

## Optimizer Lab task mapping

| Old workflow | New task |
|---|---|
| `optimizer-install-sandbox.yml` | `optimizer_install_probe` |
| `skfolio-sandbox.yml` | `skfolio_sandbox` |
| `riskfolio-dependency-sandbox.yml` | `riskfolio_dependency_probe` |
| `riskfolio-sandbox.yml` | `riskfolio_sandbox` |
| `optimizer-robustness.yml` | `optimizer_robustness` |
| `optimizer-stress-tests.yml` | `optimizer_stress_tests` |
| `apply_terminal_ia_phase2.yml` | `apply_terminal_ia_phase2` |
| `v19-technical-debt-cleanup.yml` | `technical_debt_cleanup` |
| multiple optimizer refresh workflows | `all_optimizer_outputs` |