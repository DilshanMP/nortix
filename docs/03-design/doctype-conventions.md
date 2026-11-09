---
title: "DocType Conventions"
status: "Approved"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# DocType Conventions

| Item | Convention |
| --- | --- |
| Name | Title Case, singular, business term (`Issued Item`, `Renewal`) |
| Prefix | Settings and product-specific single DocTypes start with `Nortix` |
| Module | The owning business module |
| Naming | Naming series per company where users see the ID (`ISS-.YYYY.-.#####`); hash only for child or internal records |
| Company field | `company` (Link, mandatory) on every transactional DocType; `branch` where location matters |
| Submittable | Yes for anything affecting balances, money or audit |
| Track changes | On for all custom DocTypes |
| Permissions | Defined per role in the DocType; User Permission on Company and Branch applied |
| Field level | Sensitive fields (salary, NIC) at a higher permlevel |
| Mandatory and unique | Declared in the DocType, not only in code |
| Search index | On fields used in filters and links |
| Title field | Set so lists and links read naturally |
| Description | Every custom field has a description shown in the form |
| Tests | `test_<doctype>.py` with permission and isolation tests |

## Field naming
- Dates end with `_date`; counts with `_count`; days with `_days`; amounts with `_amount`.
- Booleans start with `is_` or `has_`.
- Links are named after the target in snake_case (`employee`, `leave_type`).
