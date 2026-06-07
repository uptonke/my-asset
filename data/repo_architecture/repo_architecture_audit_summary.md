# v4.0 Repo Architecture Audit

- Generated: `2026-06-07T13:45:56.733262+00:00`
- Total files scanned: `185`
- GitHub workflow files: `8`
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
- `assets/js/app.bundle.js` — 210770 bytes
- `assets/js/quant-main-display.js` — 16932 bytes
- `assets/js/terminal-ia-phase2.js` — 212 bytes
- `assets/js/terminal-ui-polish.js` — 1203 bytes

## Review-before-delete candidates

- `postcss.config.js` — root-level JS should be reviewed before deletion
- `tailwind.config.js` — root-level JS should be reviewed before deletion

## Do-not-delete without tests

- `index.html`
- `assets/js/app.bundle.js`
- `assets/js/src/app.bundle.source.js`
- `assets/js/quant-main-display.js`
- `assets/css/tailwind-built.css`
- `.github/workflows/*.yml`
- `scripts/*.py used by workflows`
- `data/optimizer/*.json read by frontend`
