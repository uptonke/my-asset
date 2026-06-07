# v4.1 Frontend Source of Truth

## Decision

For the current transitional release, the single frontend JavaScript source of truth is:

```txt
assets/js/src/app.bundle.source.js
```

The runtime bundle is:

```txt
assets/js/app.bundle.js
```

Rule:

```txt
Edit canonical source → run build → update runtime bundle
```

Do not hand-edit:

```txt
assets/js/app.bundle.js
```

## Why this decision

The repo currently contains both:

```txt
assets/js/app.bundle.js
assets/js/src/*.js
root-level *.js fragments
```

The runtime `assets/js/app.bundle.js` contains newer frontend work than the old split fragments under `assets/js/src/00-*.js` to `60-*.js`. Therefore v4.1 does not pretend those fragments are authoritative.

Instead, v4.1 freezes the current runtime bundle into:

```txt
assets/js/src/app.bundle.source.js
```

This gives the repo one editable source while avoiding accidental loss of v2/v3 frontend additions.

## Legacy fragments

These are retained for review, but are not authoritative in v4.1/v4.2:

```txt
assets/js/src/00-bootstrap-and-cro.js
assets/js/src/10-state-auth-cloud.js
assets/js/src/20-holdings-performance.js
assets/js/src/30-risk-xray-tail.js
assets/js/src/40-actions-history-buffer.js
assets/js/src/50-montecarlo-kelly.js
assets/js/src/60-ui-and-charts.js
```

They should be either resynced or removed in a later v4.3/v4.7 pass.

## Build commands

Build runtime bundle:

```bash
python scripts/build_frontend_bundle.py
```

Check source/runtime drift:

```bash
python scripts/build_frontend_bundle.py --check
```

Run repo architecture audit:

```bash
python scripts/audit_repo_architecture.py
```

## Safety boundary

This is not a UI rewrite and not a component split. v4.1 only defines source ownership and prevents future manual runtime-bundle edits from becoming the norm.
