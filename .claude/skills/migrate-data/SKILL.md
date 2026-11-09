---
name: migrate-data
description: "Plan and build an idempotent data migration (Sheet, CSV or legacy ERP) with validation, error report and reconciliation. Use for any import of existing business data."
argument-hint: "<source> <target DocTypes>"
---

# Migrate data

1. Read docs/04-data/migration-*.md for the source.
2. Never read or print real data in the conversation; work with column names and a synthetic sample.
3. Write the transform in `nortix/<module>/migration/` with: row validation, mapping, an error report (row number + field, no personal values), and a dry-run mode.
4. Make loads idempotent (legacy IDs as keys).
5. Write the reconciliation query or report that compares results with the source totals.
6. Run on staging only. Production runs are done by the owner.
