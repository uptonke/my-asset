# scripts map

v1.9 起先採「分類，不搬移」策略，避免破壞既有 GitHub Actions import path。

## production_quant
- update_stock_meta.py
- remove_chip_core_factor.py
- update_pivot_meta.py
- fix_xray_twd_weights.py

## macro_and_compass
- update_market_compass.py
- update_weekly_official_meta.py

## optimizer_sandbox
- check_optimizer_deps.py
- check_riskfolio_deps.py
- run_skfolio_sandbox.py
- run_riskfolio_sandbox.py
- run_optimizer_robustness.py
- run_optimizer_stress_tests.py

## frontend_migration_legacy
- apply_frontend_migration.py
- apply_terminal_design_system.py
- apply_terminal_ia_phase2.py
- rollback_terminal_design_system.py

## rule
v1.9 不刪 Python 檔。v4 才做實體目錄拆分。
