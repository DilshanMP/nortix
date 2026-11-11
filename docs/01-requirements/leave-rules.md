---
title: "Leave Rules (R1)"
status: "Approved"
owner: Pasindu Dilshan
updated: 2026-11-12
source: "Leave_Managment_System_Akvora Sheet (Leave Policy, Leave Balance formulas), HR"
---

# Leave Rules (R1)

All R1 leave rules are confirmed by the product owner (LV-006 on 2026-11-11, the rest on 2026-11-12), following the leave Sheet's current policy. Where the Sheet is silent, the answer comes from the rule's own wording or from standard Frappe HR behaviour, and says so. Open items that do not change a calculation are listed under each rule and in `open-questions.md`.

The 1-year mark is the join date plus 12 months (the anniversary; a 29 Feb join date gives 28 Feb) for every rule below (Q9, Q10).

---

### LV-001 Leave types
**Status:** Confirmed 2026-11-12 by the product owner.
**Rule:** The system provides Casual, Additional, Annual and Medical leave. Names and active types are configurable.
**Acceptance:** Each type exists with its allocation rule; inactive types cannot be applied for.
**Source:** The leave Sheet's Settings tab lists exactly these four types.

### LV-002 Leave period
**Status:** Confirmed 2026-11-12 by the product owner.
**Rule:** Entitlements reset each calendar year (1 Jan to 31 Dec). Unused leave does not carry forward (Q2).
**Acceptance:**
- Each company has a Leave Period from 1 Jan to 31 Dec; allocations for a year end on 31 Dec.
- On 2027-01-01 no 2026 days are available; the four leave types have carry forward off.
- A company without an active Leave Period gets no automatic allocations and appears in the job summary.
- A Leave Period that does not run from 1 Jan to 31 Dec gets no automatic allocations and appears in the job summary, because every amount assumes the calendar year.
**Open, not blocking:** Q21 (who creates each year's Leave Period).

Automatic allocations (LV-003 to LV-007) go to employees with status Active; Inactive and Suspended are open (Q24).

### LV-003 Casual leave before the 1-year mark
**Status:** Confirmed 2026-11-12 by the product owner.
**Rule:** In the joining year: 0.5 day for each month from the join month to December inclusive, granted up front from the join date (Q3). In a later year before the 1-year mark: 6 days from the start of the period.
**Acceptance:**

| Joined | Period | Checked on | Casual days |
| --- | --- | --- | --- |
| 2026-01-01 | 2026 | 2026-01-01 | 6.0 |
| 2026-05-10 | 2026 | 2026-05-10 | 4.0 |
| 2026-05-31 | 2026 | 2026-05-31 | 4.0 (the join month counts in full) |
| 2026-12-01 | 2026 | 2026-12-01 | 0.5 |
| 2025-11-01 | 2026 | 2026-10-31 | 6.0 |

- Changing the monthly amount in Nortix Leave Settings changes new allocations only (LV-011).

### LV-004 Casual leave after the 1-year mark
**Status:** Confirmed 2026-11-12 by the product owner.
**Rule:** From the 1-year mark: 7 days per leave period. In the year of the mark the 6 days become 7 on the mark date; casual leave taken earlier in that period counts against the 7 (leave Sheet).
**Acceptance:**

| Joined | Period | Checked on | Casual days |
| --- | --- | --- | --- |
| 2025-11-01 | 2026 | 2026-10-31 | 6.0 |
| 2025-11-01 | 2026 | 2026-11-01 | 7.0 (one day added from the mark date) |
| 2024-08-10 | 2026 | 2026-01-01 | 7.0 |

- 5 days taken by 2026-10-31, mark 2026-11-01 → 2 days left.
- The daily job running twice adds the extra day once.
- The rise applies whatever created the casual allocation, including the Sheet import (the rule is the same for every employee).
- If HR has already submitted an adjustment on that allocation, the job does not add the day and lists the employee for HR review (Frappe HR allows one submitted adjustment per allocation).

### LV-005 Additional leave before the 1-year mark
**Status:** Confirmed 2026-11-12 by the product owner.
**Rule:** 1 day in each leave period before the 1-year mark (Q19), available from the later of the join date and the period start until the day before the mark. From the mark there is no additional leave; days already taken stay recorded and the balance does not go below zero (Q18).
**Acceptance:**

| Joined | Period | Checked on | Additional days |
| --- | --- | --- | --- |
| 2026-05-10 | 2026 | 2026-05-10 | 1, usable 2026-05-10 to 2026-12-31 |
| 2025-11-01 | 2026 | 2026-01-01 | 1, usable 2026-01-01 to 2026-10-31 |
| 2025-11-01 | 2026 | 2026-11-01 | no additional leave can be applied for |

- An employee who took the day before the mark shows it as taken, not as an overdraft.

### LV-006 Annual leave by quarter of the 1-year mark
**Status:** Confirmed 2026-11-11 by the product owner (leave Sheet policy).
**Rule:** From the mark date, annual leave for that period is set by the quarter the mark falls in: Jan to Mar 14, Apr to Jun 10, Jul to Sep 7, Oct to Dec 4. Before the mark date there is no annual leave. In later periods: 14. Permanent status is not required (Q1).
**Acceptance:**
- Mark 2026-11-01 → 4 days in 2026 (AKINT-022 case).
- Mark 2026-03-31 → 14; mark 2026-04-01 → 10.
- Joined 2025-04-01 → mark 2026-04-01 → 10 days in 2026.
- Joined 2024-02-29 → mark 2025-02-28 → 14 days in 2025.
- On 2026-10-31, an employee with mark 2026-11-01 has no annual leave for 2026.
- Mark in 2025, period 2026 → 14.
- The daily job running twice creates one allocation.
- Employee with a 2026 annual allocation from the migration → the job creates no second allocation for 2026 (Q16).

The criterion "employee with no join date" moved to LV-013 on 2026-11-12: the join date is mandatory on Employee, so the case exists only in the Sheet import.
**Answered:** Q1, Q2, Q9, Q10, Q11, Q17 (leave Sheet); Q16 (product owner).
**Open, not blocking:** Q12 to Q15.

### LV-007 Medical leave
**Status:** Confirmed 2026-11-12 by the product owner.
**Rule:** 7 days per leave period for all employees from joining (Q4), including the full 7 in the joining year (Q20); applications need management approval.
**Acceptance:**
- Joined 2026-05-10 → 7 medical days for 2026 from 2026-05-10.
- Joined 2025-03-01 → 7 medical days for 2026 from 2026-01-01.
- Medical applications route to the management approver.
**Open, blocking the approval route only:** Q23 (who the management approver is).

### LV-008 Leave balance
**Status:** Confirmed 2026-11-12 by the product owner.
**Rule:** Balance = allocation for the period minus approved leave days in the period. Half days are allowed (0.5 day). Only approved leave reduces the balance (Q5); pending applications are shown but do not reduce the balance at application time, as in standard Frappe HR (Q22).
**Acceptance:**

| Allocated | Approved | Open (pending) | Rejected | Balance |
| --- | --- | --- | --- | --- |
| 7 | 2.5 (includes one half day) | 1 | 2 | 4.5 |

- The balance report per employee and type equals allocation minus approved days.

### LV-009 Application and approval
**Status:** Confirmed 2026-11-12 by the product owner.
**Rule:** Employees apply on phone or web; the leave approver (reports-to manager) approves or rejects; HR can view all. Medical leave goes to the management approver (LV-007).
**Acceptance:** An employee cannot approve their own leave; rejected leave does not reduce the balance.
**Open, blocking medical routing only:** Q23.

### LV-010 Low and critical balance alerts
**Status:** Confirmed 2026-11-12 by the product owner.
**Rule:** Balance of 2 days or less is low; 0 is critical (leave Sheet thresholds).
**Acceptance:**
- HR sees both in the Leave Balance Alerts report, limited to the companies they can see (LV-012).
- Each user with the summary role receives a weekly email listing only the employees their permissions allow (Q26). The role must be an HR role; users with no company restriction are included only when the settings allow it.
- Only leave types the employee holds an allocation for on the date are checked, so an employee before the 1-year mark is not flagged for annual leave they do not have yet.
- Pending applications do not lower the balance (Q22); employees who are not Active are not listed.

### LV-011 Configurable rules
**Status:** Confirmed 2026-11-12 by the product owner.
**Rule:** Every number in LV-003 to LV-010 is set in Nortix Leave Settings, not in code. Only System Manager can change the settings, because they apply to every company (decided 2026-11-11).
**Acceptance:** Changing a quarter amount in settings changes new allocations without a code change.

### LV-012 Isolation
**Status:** Confirmed 2026-11-12 by the product owner.
**Rule:** HR users see only the companies and branches they are assigned to.
**Acceptance:** A user limited to one company cannot read another company's leave records through form, list, report, API or export.

### LV-013 Migration from the leave Sheet
**Status:** Confirmed 2026-11-12 by the product owner.
**Rule:** 57 employees and the 2026 leave records are imported; balances after import match the Sheet's confirmed balances, apart from the explained differences in Q5 (unapproved rows) and Q18 (additional leave after the mark).
**Acceptance:**
- Reconciliation report shows zero unexplained differences, signed off by HR.
- An employee with no join date in the Sheet is not imported and is listed in the import error report for HR (moved from LV-006).
**Pre-conditions:** 7 missing join dates, 17 missing companies and inconsistent company names fixed in the Sheet first (Q8).
