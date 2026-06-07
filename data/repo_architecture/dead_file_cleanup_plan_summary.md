# Dead File Cleanup Plan v4.7

- Status: **PLAN_ONLY**
- Auto delete enabled: `False`
- Safe-delete candidates existing: `0`
- Review-before-delete existing: `1`

## Safe delete candidates
- `README_FRONTEND_MIGRATION.md` — exists: `False` — root-level stale workflow/readme duplicate or migration note; not a runtime path
- `README_TERMINAL_DESIGN_SYSTEM.md` — exists: `False` — root-level stale workflow/readme duplicate or migration note; not a runtime path
- `README_V05_V06_OVERLAY.md` — exists: `False` — root-level stale workflow/readme duplicate or migration note; not a runtime path
- `daily_update.yml` — exists: `False` — root-level stale workflow/readme duplicate or migration note; not a runtime path
- `weekly_macro_update.yml` — exists: `False` — root-level stale workflow/readme duplicate or migration note; not a runtime path
- `frontend_tailwind_migration.yml` — exists: `False` — root-level stale workflow/readme duplicate or migration note; not a runtime path

## Review before delete
- `00-bootstrap-and-cro.js` — exists: `False` — root-level JS/Python candidate; delete only after confirming no external link or GitHub Pages reference
- `00-tailwind-config.js` — exists: `False` — root-level JS/Python candidate; delete only after confirming no external link or GitHub Pages reference
- `10-state-auth-cloud.js` — exists: `False` — root-level JS/Python candidate; delete only after confirming no external link or GitHub Pages reference
- `30-risk-xray-tail.js` — exists: `False` — root-level JS/Python candidate; delete only after confirming no external link or GitHub Pages reference
- `40-actions-history-buffer.js` — exists: `False` — root-level JS/Python candidate; delete only after confirming no external link or GitHub Pages reference
- `60-ui-and-charts.js` — exists: `False` — root-level JS/Python candidate; delete only after confirming no external link or GitHub Pages reference
- `app.bundle.js` — exists: `False` — root-level JS/Python candidate; delete only after confirming no external link or GitHub Pages reference
- `quant-main-display.js` — exists: `False` — root-level JS/Python candidate; delete only after confirming no external link or GitHub Pages reference
- `backup.py` — exists: `True` — root-level JS/Python candidate; delete only after confirming no external link or GitHub Pages reference

## Do not delete
- `index.html` — exists: `True`
- `assets/js/app.bundle.js` — exists: `True`
- `assets/js/src/app.bundle.source.js` — exists: `True`
- `assets/js/quant-main-display.js` — exists: `True`
- `assets/css/tailwind-built.css` — exists: `True`
- `.github/workflows/optimizer-lab.yml.yml` — exists: `True`
- `.github/workflows/validation-gate.yml.yml` — exists: `True`
- `.github/workflows/repo-architecture-audit.yml.yml` — exists: `True`
- `scripts/validate_repo_integrity.py` — exists: `True`
- `scripts/build_frontend_bundle.py` — exists: `True`
- `schemas/schema_registry.json` — exists: `True`
