# v3.8.4 / v3.8.5

- Refresh success, freshness and reported coverage are separate. Daily/monthly limits are 5/45 UTC calendar days; coverage review thresholds are 98–102%, not certified completeness. Future and regressing source dates are rejected. Existing cache remains usable as provisional research. HTTP retry is bounded; IFRA slug and COPX header alternatives are candidates, not live-verified fixes. Vanguard 404 still requires a verified full holdings endpoint or approved alternative.
- Archive first successfully observed snapshot per UTC day under data/holdings/archive. Its path is observation date, not publication or effective date; no historical dates are backfilled. Archive growth must be monitored. This is not a point-in-time universe database.
- Original security HHI remains unchanged. Issuer proxy HHI is conditional on mapped equity; curated Alphabet and Berkshire ISIN/CUSIP groups are merged; all other securities remain separate. Confirmed mapping coverage uses mapped equity denominator, not all NAV. No ticker/name heuristics. Unmapped and stale exposures remain provisional. No automatic execution.
- v3.9.1 and v3.9.2 not included in this change.

## v3.8.6 source recovery

- IFRA issuer CSV now exposes Market Weight and Notional Weight; parse market weight (not notional) and retain legacy columns. Official CSV dated 2026-11-25 verified at https://www.ishares.com/us/products/294315/ishares-u-s-infrastructure-etf/latest-holdings.csv.
- VOO/VEA try the candidate Vanguard vmf/api path before legacy endpoint. Require consistent pagination dates/counts and reject duplicate IDs and unusually small full holdings lists (400/2500). New path not independently live verified.
- COPX tries recent dated official asset CDN files using the existing observed filename convention; 404-only date probing is bounded. Reject incomplete CSVs or conflicting source dates. Product page fallback remains. Recent CDN file availability not live verified.
- All existing freshness, regression, coverage and archive checks remain. No third-party supplier added. Actual four-fund recovery must be checked on Actions; mock regression tests do not establish live availability.

## v3.8.7 Vanguard position normalization

- Missing or placeholder ISIN/CUSIP/SEDOL values no longer collide; use another syntactically valid security identifier or a snapshot-local row ID. No cross-fund merge for unknown identities.
- Distinct positions sharing a valid identifier and identical ticker/name may be aggregated with weight-mass preservation. Identical raw rows, indistinguishable economic positions and conflicting identity labels are rejected. If merging or unknown identifiers occur, a second page size must reproduce the entire raw snapshot. Coverage guard 90–100.5% is a conservative research assumption, not proof of complete coverage; no renormalization.
- A read-only PR-only VEA live probe runs on the v3.8.7 research branch. It uses a temporary directory, no credentials, no Git commits, and no Supabase write. Live recovery is not established until this check succeeds. Existing cache remains unchanged on failure.
