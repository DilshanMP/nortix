---
title: "Database Architecture"
status: "Approved"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Database Architecture

## Engine and layout
- MariaDB, as supported by ERPNext v16. One database per site (customer organisation).
- Frappe maps each DocType to a table named `tab<DocType>`; child tables carry `parent`, `parenttype`, `parentfield`.
- Schema changes come only from DocType JSON (`bench migrate`) and patches. No manual `ALTER TABLE`.

## Integrity
| Concern | How it is enforced |
| --- | --- |
| References | Link fields validated by Frappe on save; deletion blocked while linked |
| Uniqueness | `unique` field property or composite checks in `validate` plus a unique index added by patch for critical keys |
| Required data | `reqd` in DocType JSON |
| Transactions | Each request and each job runs in one transaction; errors roll back fully |
| Concurrency | Document `modified` timestamp check prevents lost updates; `for_update` locks in services that read-then-write balances |
| Immutability | Submitted documents are read-only; corrections by cancel and amend |
| History | Track changes (Version), Activity Log, Access Log |

## Indexing
- `search_index` on fields used in filters, links and joins (`employee`, `company`, `from_date`, `leave_type`).
- Composite indexes added by patch when a report is measured slow.
- Every report is tested with production-sized data on staging before release.

## Data boundaries
- Every transactional row carries `company`; queries go through permission-aware APIs.
- Sensitive fields (salary, NIC, bank details) at higher permlevels and excluded from list views and exports by default.

## Backups and retention
- Daily encrypted offsite backup of database and files; retention 30 daily, 12 monthly (to approve).
- Monthly restore test on staging, timed against RTO.
- Retention per data class in `data-classification.md`.

## Migrations
- Patches in `nortix/patches/`, listed in `patches.txt`, each idempotent and tested on a staging copy.
- A pre-migration backup is taken automatically before every production `bench migrate`.
