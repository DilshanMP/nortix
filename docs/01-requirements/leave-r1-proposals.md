---
title: "Leave R1: Proposed Acceptance Criteria (LV-002 to LV-008)"
status: "Draft"
owner: Pasindu Dilshan
updated: 2026-11-12
---

# Leave R1: Proposed Acceptance Criteria (LV-002 to LV-008)

LV-002, LV-003 and LV-004 have enough answers to be confirmed with the criteria below; LV-005 and LV-007 each need one HR answer first, and LV-008 needs one confirmation. Nothing here changes `leave-rules.md` until the product owner approves it.

Sources: the leave Sheet's Leave Policy tab and Leave Balance formulas (read 2026-11-11), the answers in `open-questions.md`, and the LV-006 build. Every example uses synthetic dates, not real employees.

## Status at a glance

| Requirement | Ready to confirm? | Blocking question |
| --- | --- | --- |
| LV-002 Leave period | Yes, after Q21 | Q21 (who creates each year's Leave Period) |
| LV-003 Casual before the mark | Yes | None |
| LV-004 Casual after the mark | Yes | None |
| LV-005 Additional before the mark | No | Q18, Q19 |
| LV-007 Medical | No | Q20 |
| LV-008 Balance | Yes, after Q22 | Q22 (pending applications) |

## Proposed acceptance criteria

### LV-002 Leave period
- Each company has a Leave Period from 1 Jan to 31 Dec; allocations for a year end on 31 Dec.
- On 2027-01-01 no 2026 days are available (no carry forward, Q2); the Casual, Additional, Annual and Medical leave types have carry forward off.
- A company without an active Leave Period gets no automatic allocations and appears in the job summary (as built for LV-006).

### LV-003 Casual leave before the 1-year mark
The joining-year amount is granted up front from the join date, counting the join month (Q3): 0.5 × (13 − join month).

| Joined | Period | Checked on | Casual days |
| --- | --- | --- | --- |
| 2026-01-01 | 2026 | 2026-01-01 | 6.0 |
| 2026-05-10 | 2026 | 2026-05-10 | 4.0 |
| 2026-05-31 | 2026 | 2026-05-31 | 4.0 (May counts in full) |
| 2026-12-01 | 2026 | 2026-12-01 | 0.5 |
| 2025-11-01 | 2026 | 2026-10-31 | 6.0 (later year, mark not reached) |

- Changing the monthly amount in Nortix Leave Settings changes new allocations only (LV-011).

### LV-004 Casual leave after the 1-year mark
| Joined | Period | Checked on | Casual days |
| --- | --- | --- | --- |
| 2025-11-01 | 2026 | 2026-10-31 | 6.0 |
| 2025-11-01 | 2026 | 2026-11-01 | 7.0 (one day added from the mark date) |
| 2024-08-10 | 2026 | 2026-01-01 | 7.0 |

- Casual leave taken before the mark in the mark year counts against the 7 (Sheet). Example: 5 taken by 2026-10-31, mark 2026-11-01 → 2 left.
- The daily job running twice adds the extra day once.

### LV-005 Additional leave before the 1-year mark
| Joined | Period | Checked on | Additional days |
| --- | --- | --- | --- |
| 2026-05-10 | 2026 | 2026-05-10 | 1 |
| 2025-11-01 | 2026 | 2026-10-31 | 1 (if Q19 is "per period") |
| 2025-11-01 | 2026 | 2026-11-01 | No new additional leave can be applied for |

- Additional leave already taken before the mark stays recorded; how it shows after the mark depends on Q18.

### LV-007 Medical leave
- An employee has 7 medical days per period from joining (Q4); a December joiner's amount depends on Q20.
- A medical application goes to the management approver, not the reporting manager (LV-009).

### LV-008 Leave balance
| Allocated | Approved | Open (pending) | Rejected | Balance |
| --- | --- | --- | --- | --- |
| 7 | 2.5 (includes one half day) | 1 | 2 | 4.5 |

- Rejected and cancelled applications do not reduce the balance (Q5).
- Whether an employee can apply for more than balance minus pending depends on Q22.

## New questions

| # | Question | Owner | Blocks |
| --- | --- | --- | --- |
| Q18 | After the 1-year mark the Sheet sets additional leave to 0, so a day taken before the mark shows as 1 day over ("Exceed"). Should the system show 0 left with the day recorded as taken, or keep the Sheet's negative balance? | HR | LV-005 |
| Q19 | Is the 1 additional day given in each leave period before the mark (the Sheet's formula gives 1 in the joining year and 1 again in the next year until the mark) or once in total? | HR | LV-005 |
| Q20 | Does an employee who joins mid-year get all 7 medical days in the joining year, or a share by months worked? The Sheet does not calculate medical leave. | HR | LV-007 |
| Q21 | Who creates each year's Leave Period for the six companies: HR in December, or the system automatically? | Product owner | LV-002 |
| Q22 | When applying, should pending applications count against the balance so an employee cannot book more than they have left? In the installed Frappe HR version the check at application time uses approved leave only (pending days are shown separately), so two open applications can together exceed the balance until one is approved. | HR | LV-008 |

The Sheet's Leave Policy also lists a 7-day cap on casual plus additional leave in the first year. No formula uses it, and the amounts above can never exceed it (at most 6 + 1), so no separate rule is proposed.

## Design notes for planning (not requirements)
- Casual, additional and medical allocations can follow the LV-006 pattern: standard Leave Allocation, one daily job, settings for every number, and the `nortix_source` field.
- The extra casual day at the mark uses Frappe HR's existing way of adding days to a submitted allocation from a date, so there is still one allocation per employee, leave type and period.
