---
title: "Migration Plan: Leave Sheet to Nortix"
status: "Draft"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Migration Plan: Leave Sheet to Nortix

Three tabs carry source data; everything else in the Sheet is calculated and is rebuilt by the system.

| Sheet tab | Rows | Target |
| --- | --- | --- |
| Employee Master | 57 | Employee (+ Company, Branch, Department, Designation masters) |
| Leave Transactions | 434 (2026; 385 Approved, 48 UnApproved, 1 blank) | Leave Application for leave period 2026 |
| Leave Policy, Settings | Rule values, system year, lists | Nortix Leave Settings, Leave Types, Leave Period 2026, Holiday List |
| Leave Balance and views | Calculated | Not imported; used for reconciliation |

## Steps
1. **Clean the source** (HR confirms each fix): 7 missing join dates; 17 missing companies; company names standardised to the six Company records; trailing spaces in department and branch; status values mapped (UnApproved → Open, blank → Open with HR review).
2. **Export** each tab to CSV into `data/raw/` (git-ignored). Never commit real data.
3. **Transform** with a script in `nortix/hr_leave/migration/` that validates every row and writes import files plus an error report.
4. **Load on staging**: masters, employees, settings, allocations (by the normal rules), then 2026 applications.
5. **Reconcile**: compare balance per employee and leave type with the Sheet; every difference is explained or fixed.
6. **Sign-off** by HR; repeat on production in a maintenance window with a fresh backup.
7. **Parallel month**: both systems run; the Sheet becomes read-only afterwards.

## Evidence
Reconciliation report and sign-off stored in `docs/testing/evidence/R1/` (with personal data removed).
