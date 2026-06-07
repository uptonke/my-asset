# v4.1 Frontend Source of Truth

- Canonical source: `assets/js/src/app.bundle.source.js`
- Runtime bundle: `assets/js/app.bundle.js`
- Legacy fragments: `assets/js/src/00-*.js` to `60-*.js` are retained for reference but are not authoritative in v4.1.
- Rule: edit canonical source, then run `python scripts/build_frontend_bundle.py`.
- Rule: do not hand-edit `assets/js/app.bundle.js`.
