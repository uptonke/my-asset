# v9.4 Manual Approval Console

v9.4 normalizes `config/manual_approval_override.json` into a review-only console output. It records manual review inputs, missing cash / budget fields, approved / rejected candidate IDs, and whether upstream gates still block formal drafts.

Boundary:
- Does not approve trades.
- Does not submit broker orders.
- Does not enable execution, trade signals, official rebalance, or broker submission.
