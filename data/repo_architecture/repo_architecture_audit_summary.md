# v4.0 Repo Architecture Audit

- Generated: `2026-06-07T08:17:09.437443+00:00`
- Total files scanned: `135`
- GitHub workflow files: `6`
- Optimizer output files: `31`

## v4.1 Frontend Source of Truth

- Policy: `canonical_single_bundle_source`
- Canonical source: `assets/js/src/app.bundle.source.js`
- Runtime bundle: `assets/js/app.bundle.js`
- Runtime matches canonical source: `True`

## Runtime files referenced by index.html

- `assets/css/00-base.css` — 8871 bytes
- `assets/css/10-components.css` — 6486 bytes
- `assets/css/20-dashboard.css` — 2 bytes
- `assets/css/30-ios-bloomberg.css` — 5274 bytes
- `assets/css/40-executive-institutional.css` — 6866 bytes
- `assets/css/50-bloomberg-terminal-hard.css` — 10122 bytes
- `assets/css/60-design-token-denoise.css` — 2375 bytes
- `assets/css/70-terminal-design-system.css` — 5739 bytes
- `assets/css/90-typography.css` — 6326 bytes
- `assets/css/tailwind-built.css` — 1950878 bytes
- `assets/js/app.bundle.js` — 205768 bytes
- `assets/js/quant-main-display.js` — 16952 bytes
- `assets/js/terminal-ia-phase2.js` — 212 bytes
- `assets/js/terminal-ui-polish.js` — 1203 bytes

## Review-before-delete candidates

- `00-bootstrap-and-cro.js` — same filename exists under assets/js/src; same filename exists under assets/js
- `00-tailwind-config.js` — same filename exists under assets/js
- `10-state-auth-cloud.js` — same filename exists under assets/js/src; same filename exists under assets/js
- `30-risk-xray-tail.js` — same filename exists under assets/js/src; same filename exists under assets/js
- `40-actions-history-buffer.js` — same filename exists under assets/js/src; same filename exists under assets/js
- `60-ui-and-charts.js` — same filename exists under assets/js/src; same filename exists under assets/js
- `app.bundle.js` — same filename exists under assets/js; root bundle conflicts with runtime bundle assets/js/app.bundle.js
- `postcss.config.js` — root-level JS should be reviewed before deletion
- `quant-main-display.js` — same filename exists under assets/js; index.html references assets/js/quant-main-display.js, not root quant-main-display.js
- `tailwind.config.js` — root-level JS should be reviewed before deletion
- `daily_update.yml` — workflow-like YAML outside .github/workflows; GitHub Actions will not execute it from root
- `frontend_tailwind_migration.yml` — workflow-like YAML outside .github/workflows; GitHub Actions will not execute it from root
- `weekly_macro_update.yml` — workflow-like YAML outside .github/workflows; GitHub Actions will not execute it from root

## Do-not-delete without tests

- `index.html`
- `assets/js/app.bundle.js`
- `assets/js/src/app.bundle.source.js`
- `assets/js/quant-main-display.js`
- `assets/css/tailwind-built.css`
- `.github/workflows/*.yml`
- `scripts/*.py used by workflows`
- `data/optimizer/*.json read by frontend`
