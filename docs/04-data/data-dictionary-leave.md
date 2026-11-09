---
title: "Data Dictionary: Leave (R1)"
status: "Draft"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Data Dictionary: Leave (R1)

Standard Frappe HR DocTypes are used as they are. Only the items below are added.

## Nortix Leave Settings (Single)

| Field | Type | Default | Rule |
| --- | --- | --- | --- |
| casual_monthly_days_first_year | Float | 0.5 | LV-003 |
| casual_days_before_mark | Float | 6 | LV-003 |
| casual_days_after_mark | Float | 7 | LV-004 |
| additional_days_before_mark | Float | 1 | LV-005 |
| annual_q1_days | Float | 14 | LV-006 |
| annual_q2_days | Float | 10 | LV-006 |
| annual_q3_days | Float | 7 | LV-006 |
| annual_q4_days | Float | 4 | LV-006 |
| annual_full_days | Float | 14 | LV-006 |
| annual_requires_permanent | Check | 1 | LV-006, Q1 |
| medical_days | Float | 7 | LV-007 |
| low_balance_days | Float | 2 | LV-010 |
| critical_balance_days | Float | 0 | LV-010 |
| casual_leave_type, additional_leave_type, annual_leave_type, medical_leave_type | Link Leave Type | | LV-001 |

## Custom fields on Employee

| Field | Type | Purpose |
| --- | --- | --- |
| nic_number | Data, permlevel 1 | Identity; restricted personal |
| legacy_employee_id | Data, unique | Mapping to the Sheet and legacy ERP |

Confirmation date uses the standard `final_confirmation_date` field on Employee.

## Custom fields on Leave Allocation

| Field | Type | Purpose |
| --- | --- | --- |
| nortix_source | Select (first_year_annual, migration, manual) | Idempotency and audit of automatic allocations |
