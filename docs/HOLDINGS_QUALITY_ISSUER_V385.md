# v3.8.4 / v3.8.5

- Refresh success, freshness and reported coverage are separate. Daily/monthly limits are 5/45 UTC calendar days; coverage review thresholds are 98–102%, not certified completeness. Future and regressing source dates are rejected. Existing cache remains usable as provisional research. HTTP retry is bounded; IFRA slug and COPX header alternatives are candidates, not live-verified fixes. Vanguard 404 still requires a verified full holdings endpoint or approved alternative.
- Archive first successfully observed snapshot per UTC day under data/holdings/archive. Its path is observation date, not publication or effective date; no historical dates are backfilled. Archive growth must be monitored. This is not a point-in-time universe database.
- Original security HHI remains unchanged. Issuer proxy HHI is conditional on mapped equity; curated Alphabet and Berkshire ISIN/CUSIP groups are merged; all other securities remain separate. Confirmed mapping coverage uses mapped equity denominator, not all NAV. No ticker/name heuristics. Unmapped and stale exposures remain provisional. No automatic execution.
- v3.9.1 and v3.9.2 not included in this change.
