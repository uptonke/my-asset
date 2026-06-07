# Dead File Cleanup v4.7

This release generates a cleanup plan only. It does not delete files automatically.

## Policy

Delete files only after:

1. Validation Gate is green.
2. GitHub Pages loads normally.
3. Runtime entrypoints are confirmed.
4. The file is listed as safe-delete, not review-before-delete.

Root-level JS files are review-before-delete, not automatic-delete, because external links or legacy GitHub Pages paths may still exist.
