---
title: "UX Guidelines"
status: "Approved"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# UX Guidelines

- **One workspace per department**, showing only that department's shortcuts, reports and number cards.
- **Role-based screens.** A staff member, an HR officer and a director see different dashboards.
- **Phone first for staff:** leave application, balance, check-in and payslip in two taps from the Frappe HR app.
- **Clear errors:** every validation message says what is wrong and how to fix it (`Annual leave balance is 2 days; you requested 3.`).
- **Empty and loading states** on custom pages and reports.
- **Server-side paging and filters** on every list.
- **Accessibility:** labels on all fields, keyboard operation, visible focus, readable contrast (WCAG 2.2 AA as the target).
- **Language:** plain business words used by HR and Finance; avoid technical terms in labels.
- **Hiding is not security:** every hidden field or button is also protected on the server.

## Journeys to prototype in Phase 3
1. Staff applies for leave on the phone and sees the remaining balance.
2. Manager approves or rejects with a reason.
3. HR reviews low and critical balances for one company.
4. HR imports the Sheet and reviews the reconciliation report.
