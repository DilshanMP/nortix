---
title: "Leave Rules (R1)"
status: "Draft"
owner: Pasindu Dilshan
updated: 2026-11-09
source: "Leave_Managment_System_Akvora Sheet (Leave Policy, Leave Balance formulas), HR"
---

# Leave Rules (R1)

These rules are taken from the current leave Sheet. Each stays Draft until HR confirms it. Questions marked **Q** must be answered before build.

---

### LV-001 Leave types
**Rule:** The system provides Casual, Additional, Annual and Medical leave. Names and active types are configurable.
**Acceptance:** Each type exists with its allocation rule; inactive types cannot be applied for.

### LV-002 Leave period
**Rule:** Entitlements reset each calendar year (1 Jan to 31 Dec).
**Acceptance:** Allocations are created per leave period; a new period starts on 1 Jan.
**Q:** Does unused leave carry forward? If yes, which types and how many days?

### LV-003 Casual leave before the 1-year mark
**Rule:** In the joining year: 0.5 day for each month from the join month to December inclusive. In a later year before the 1-year mark: 6 days.
**Acceptance:**
- Joined 2026-05-10, period 2026 → 4 days (May to Dec = 8 months × 0.5).
- Joined 2025-11-01, period 2026, mark not reached on the date checked → 6 days.
**Q:** Is the 0.5 per month earned monthly (accrual) or granted up front for the year?

### LV-004 Casual leave after the 1-year mark
**Rule:** From the 1-year mark: 7 days per leave period.
**Acceptance:** Employee whose mark has passed has 7 days of casual leave for the period.
**Q:** In the year the mark falls, is it 7 days in full or 7 days minus casual already granted?

### LV-005 Additional leave before the 1-year mark
**Rule:** 1 day while the 1-year mark has not been reached; 0 after.
**Acceptance:** Allocation stops at the mark; days already taken remain recorded.

### LV-006 Annual leave by quarter of the 1-year mark
**Rule:** When the 1-year mark is reached, annual leave for that period is set by the quarter the mark falls in: Jan to Mar 14, Apr to Jun 10, Jul to Sep 7, Oct to Dec 4. In later periods: 14.
**Acceptance:**
- Mark 2026-11-01 → 4 days in 2026 (AKINT-022 case).
- Mark 2026-03-31 → 14; mark 2026-04-01 → 10.
- Mark not yet reached → 0.
- Mark in 2025, period 2026 → 14.
- The daily job running twice creates one allocation.
**Q:** Is Permanent status required in addition to the mark (the Sheet requires it today)?

### LV-007 Medical leave
**Rule:** 7 days per leave period; applications need management approval.
**Acceptance:** Medical applications route to the management approver.
**Q:** From when is an employee eligible: joining, or the 1-year mark? (The Sheet does not calculate it.)

### LV-008 Leave balance
**Rule:** Balance = allocation for the period minus approved leave days in the period.
**Acceptance:** The balance report per employee and type equals allocation minus approved days.
**Q:** Are half days allowed? Do pending applications reduce the available balance?

### LV-009 Application and approval
**Rule:** Employees apply on phone or web; the leave approver (reports-to manager) approves or rejects; HR can view all.
**Acceptance:** An employee cannot approve their own leave; rejected leave does not reduce the balance.

### LV-010 Low and critical balance alerts
**Rule:** Balance of 2 days or less is low; 0 is critical.
**Acceptance:** HR sees both in a report and receives a weekly summary.

### LV-011 Configurable rules
**Rule:** Every number in LV-003 to LV-010 is set in Nortix Leave Settings, not in code.
**Acceptance:** Changing a quarter amount in settings changes new allocations without a code change.

### LV-012 Isolation
**Rule:** HR users see only the companies and branches they are assigned to.
**Acceptance:** A user limited to one company cannot read another company's leave records through form, list, report or API.

### LV-013 Migration from the leave Sheet
**Rule:** 57 employees and the 2026 leave records are imported; balances after import match the Sheet's confirmed balances.
**Acceptance:** Reconciliation report shows zero unexplained differences, signed off by HR.
**Pre-conditions:** 7 missing join dates, 17 missing companies and inconsistent company names fixed in the Sheet first.
