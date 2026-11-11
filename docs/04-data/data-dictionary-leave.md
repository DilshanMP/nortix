---
title: "Data Dictionary: Leave (R1)"
status: "Draft"
owner: Pasindu Dilshan
updated: 2026-11-12
---

# Data Dictionary: Leave (R1)

Standard Frappe HR DocTypes are used as they are. Only the items below are added.

## Nortix Leave Settings (Single)

| Field | Type | Default | Rule |
| --- | --- | --- | --- |
| is_casual_allocation_enabled | Check | 0 | LV-003, LV-004; turned on after the Sheet import (LV-013) |
| casual_monthly_days_first_year | Float | 0.5 | LV-003 |
| casual_days_before_mark | Float | 6 | LV-003 |
| casual_days_after_mark | Float | 7 | LV-004 |
| is_additional_allocation_enabled | Check | 0 | LV-005; turned on after the Sheet import (LV-013) |
| additional_days_before_mark | Float | 1 | LV-005 |
| is_annual_allocation_enabled | Check | 0 | LV-006; turned on after the Sheet import (LV-013) |
| annual_q1_days | Float | 14 | LV-006 |
| annual_q2_days | Float | 10 | LV-006 |
| annual_q3_days | Float | 7 | LV-006 |
| annual_q4_days | Float | 4 | LV-006 |
| annual_full_days | Float | 14 | LV-006 |
| annual_requires_permanent | Check | 0 | Not built: Permanent status is not required (Q1) |
| is_medical_allocation_enabled | Check | 0 | LV-007; turned on after the Sheet import (LV-013) |
| medical_days | Float | 7 | LV-007 |
| medical_leave_approver | Link User (HR role required) | | LV-007, Q23: receives new medical applications |
| medical_backup_approvers | Table MultiSelect: Nortix Medical Backup Approver (user) | | LV-007, Q23: may approve when HR is away; must hold Leave Approver or an HR role; HR emailed on each decision |
| is_balance_alert_enabled | Check | 0 | LV-010 weekly summary |
| balance_alert_role | Link Role | HR Manager | LV-010 summary recipients; HR roles only (Q26, T12) |
| is_balance_alert_to_unrestricted | Check | 0 | LV-010; also email users with no company restriction (Q26) |
| low_balance_days | Float | 2 | LV-010 |
| critical_balance_days | Float | 0 | LV-010 |
| casual_leave_type, additional_leave_type, annual_leave_type, medical_leave_type | Link Leave Type | | LV-001 |

## Custom fields on Employee

| Field | Type | Purpose |
| --- | --- | --- |
| nic_number | Data, permlevel 1 | Identity; restricted personal |
| legacy_employee_id | Data, unique | Mapping to the Sheet and legacy ERP |

The 1-year mark is computed as `date_of_joining` plus 12 months (Q9, Q10); `final_confirmation_date` is not used for leave.

## Custom fields on Leave Allocation

| Field | Type | Purpose |
| --- | --- | --- |
| nortix_source | Select (annual_rule, casual_rule, additional_rule, medical_rule, migration, manual), read only, not copied on amend | Audit of how an allocation was created; a cancelled allocation from a leave rule stops the daily job recreating it (LV-003 to LV-007) |

The extra casual day at the 1-year mark (LV-004) is a standard Leave Adjustment on the casual allocation, posted on the mark date and marked `casual_rule`. Only the job's own adjustment, submitted or cancelled, counts as done. A submitted adjustment made by HR leaves no room for another (Frappe HR allows one per allocation), so the job logs the employee under "Leave allocation needs review" instead.

## Custom fields on Leave Adjustment

| Field | Type | Purpose |
| --- | --- | --- |
| nortix_source | Select (casual_rule), read only, not copied on amend | Marks the casual rise the daily job adds at the 1-year mark (LV-004); set by server code only |

## Nortix Holiday Year (LV-014)

One record per calendar year (2000 to next year); saving it rebuilds the shared calendar. Site-wide configuration (one calendar for all companies, Q29), so it has no company field. Only HR Managers and System Managers without a company restriction can change it (Q31); HR users and employees can read it.

| Field | Type | Purpose |
| --- | --- | --- |
| year | Int, unique, set once | The calendar year |
| holiday_list | Link Holiday List, read only | The built list, named `Nortix <year>` |
| holidays | Table: Nortix Mercantile Holiday (holiday_date, description) | Gazetted mercantile holidays entered by HR |

The built Holiday List has every Sunday as a weekly off, every Saturday as a half-day weekly off, and each mercantile holiday as a full day. It is assigned to every company from 1 January through Holiday List Assignment; a company that already has another calendar from that date is logged under "Holiday calendar needs review" instead of being changed. Leave Application counts a Saturday as 0.5 day through a nortix override of the leave-day count (LV-014, Q28).
