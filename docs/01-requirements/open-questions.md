---
title: "Open Questions and Decisions"
status: "Draft"
owner: Pasindu Dilshan
updated: 2026-11-11
---

# Open Questions and Decisions

| # | Question | Owner | Blocks | Answer |
| --- | --- | --- | --- | --- |
| D2 | ERP-stage platform: decided after the legacy ERP requirements analysis | Management | ERP stage | |
| D3 | Hosting: managed cloud outside Sri Lanka acceptable under the PDPA? | Management | Go-live | |
| D4 | Security target ASVS 5.0 Level 2 for custom code | Product owner | R1 build | |
| D5 | RPO 24 h / RTO 4 h now; RPO 1 h from payroll | Management | R1 go-live | |
| D6 | Second admin and backup key holder | Management | R1 go-live | |
| D7 | Product name: Nortix chosen 2026-11-09. Web searches found the name in use elsewhere, including NortixLabs (software and SaaS), Nortix Informática (Brazil, IT) and Nortix Launcher (games). Domain, WIPO and NIPO checks required before public launch; customer sites use their own brand (ADR-0006) | Product owner | Public launch | Nortix |
| D9 | Customer brand for Akvora Group (proposal: "Akvora One") | Management | R1 go-live | |
| D8 | IP ownership and licensing of the product (built at Akvora, offered to others); GPL-3.0 obligations of ERPNext/Frappe HR | Management, legal | Offering to other companies; publishing code | |
| Q1 | Annual leave: Permanent status required in addition to the 1-year mark? If yes: which field records Permanent; when confirmation comes after the mark, does the quarter follow the mark or the confirmation date; and if confirmation falls in the next year, is that year 14 days or a quarter amount? | HR | LV-006 | 2026-11-11, leave Sheet (current Leave Balance formula): No. Annual leave depends only on the 1-year mark (Q9); employment status, confirmation status and Permanent Date are not used. An older formula kept in the hidden Backup_AnnualEligible tab required Permanent status and took the quarter from Permanent Date plus 12 months; it has been replaced |
| Q2 | Carry forward of unused leave? For annual leave this matters most for a mark in Oct to Dec, which gives 4 days usable for a few weeks before 31 Dec | HR | LV-002, LV-006 | 2026-11-11, leave Sheet: No carry forward. Entitlements are computed for the current year only |
| Q3 | Casual leave: monthly accrual or up front? | HR | LV-003 | 2026-11-11, product owner: up front, as the leave Sheet calculates (0.5 × months from the join month to December, available at once). The Sheet's Leave Policy note "earned monthly per completed month" is not followed |
| Q4 | Medical leave eligibility start | HR | LV-007 | 2026-11-11, leave Sheet (Leave Policy tab): from joining. The rule applies to "All employees"; the Sheet does not compute a medical balance |
| Q5 | Half days; pending applications reduce available balance? | HR | LV-008 | 2026-11-11: half days allowed (leave Sheet). Product owner: only approved leave reduces the balance. The Sheet counts all rows, including 79 UnApproved in 2026; migration reconciliation (LV-013) must explain that difference |
| Q6 | Attendance machine model, count, sites; ADMS push support | IT | R2 | |
| Q7 | Payroll components, current tool, banks | HR, Finance | R2 | |
| Q8 | Correct company and dates for the 7 + 17 incomplete employee records | HR | LV-013 | |
| Q9 | Which date is the 1-year mark: join date plus 12 months (glossary) or the confirmation date HR records in `final_confirmation_date` (data dictionary)? If the confirmation date, what applies when it is blank? | HR | LV-003 to LV-006 | 2026-11-11, leave Sheet: join date plus 12 months, computed (Employee Master "Confirmation Date" is `EDATE(Join Date, 12)`). No HR-entered date is used; with no join date there is no entitlement |
| Q10 | Is the mark the anniversary or the day the first year is completed? Joined 1 Apr 2025: is 2026 annual leave 10 days (mark 1 Apr) or 14 (mark 31 Mar)? Joined 29 Feb 2024: what is the mark date? | HR | LV-006 | 2026-11-11, leave Sheet: the anniversary (`EDATE`). Joined 1 Apr 2025 → mark 1 Apr 2026 → 10 days. Joined 29 Feb 2024 → mark 28 Feb 2025 (`EDATE` uses the last day of a shorter month) |
| Q11 | In the year of the mark, can annual leave be taken only from the mark date, or from 1 Jan? | HR | LV-006 | 2026-11-11, leave Sheet: from the mark date. Annual entitlement is 0 on any day before the mark |
| Q12 | Is the quarter rule (14, 10, 7, 4) company policy or a statutory entitlement? If statutory, may a customer set lower values, and do the values belong in `localisation/lk` (ADR-0005) rather than Nortix Leave Settings? | HR, Management | LV-006, LV-011 | |
| Q13 | When an employee moves between companies in the group, does the 1-year mark run from the first join date or from the join date at the new company? | HR | LV-003 to LV-006 | |
| Q14 | Is annual leave pro-rated in the year an employee leaves? Does a rehired employee start a new 1-year mark? | HR | LV-006 | |
| Q15 | When a join or confirmation date is corrected after an allocation exists, should the system flag the allocation for HR to correct, or cancel and re-allocate automatically? | HR, Product owner | LV-003 to LV-006, LV-013 | |
| Q16 | When the daily allocation job finds a 2026 annual allocation created by the migration, does it skip that employee for 2026? | Product owner | LV-006, LV-013 | |
| Q17 | Can "mark not yet reached → 0" be stated as "on any date before the mark, the employee has no annual allocation for that period"? | HR | LV-006 | 2026-11-11, leave Sheet: yes (see Q11) |
