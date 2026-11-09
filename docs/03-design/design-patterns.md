---
title: "Design Patterns"
status: "Approved"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Design Patterns

The patterns below are applied the Frappe way. Each one names where it lives and why it is used.

| Pattern | Where | Why |
| --- | --- | --- |
| Modular monolith | `nortix/<module>/` | One deployable app, clear business boundaries |
| Layered (thin controller, service layer) | `doctype/*.py` calls `services/*.py` | Business rules testable without UI or HTTP |
| Aggregate | A DocType with its child tables | One consistency boundary per document (Leave Application, Payroll Entry) |
| Settings singleton | `Nortix Leave Settings` (Single DocType) | Configuration over code (ADR-0004) |
| Strategy | `localisation/<country>/` behind a common interface | Swap statutory rules per country (ADR-0005) |
| Observer | `doc_events` in `hooks.py` | React to core document events without editing core |
| Template method | Controller lifecycle: `validate`, `before_submit`, `on_submit`, `on_cancel` | Fixed order of checks and side effects |
| Command / job | `frappe.enqueue`, scheduler events | Long or periodic work outside the request |
| Idempotency key | Unique fields such as (employee, leave_type, period, source) | Safe retries of jobs and imports |
| Immutable record + reversal | Submittable DocTypes; cancel and amend | Audit trail for leave, payroll and money |
| Query object | `frappe.qb` builders in `services/queries.py` | Safe, reusable, permission-aware queries |
| Adapter | `integrations/<system>.py` | Isolate device, bank and legacy formats |
| Migration script | `patches/` + `patches.txt` | Versioned, repeatable data changes |

## Example: annual leave allocation (LV-006)

```text
scheduler (daily)
  -> hr_leave.services.annual.allocate_due_annual_leave(on_date)
       reads Nortix Leave Settings
       finds employees whose 1-year mark <= on_date and no allocation exists for (employee, Annual, period, "first_year")
       for each: get_quarter_entitlement(mark_date, period_year, settings)
                 create and submit Leave Allocation
       returns a summary for the job log
```

The controller of Leave Allocation is not changed; the service uses the standard DocType, so balances and reports keep working.

## Anti-patterns to avoid
- Business logic in form scripts or client-side code.
- Customer names or numbers in `if` statements.
- Reading another module's tables directly instead of its services.
- Editing submitted documents through `db_set` to "fix" figures.
- Server Scripts created in the UI and never moved into the app.
