---
title: "Requirements Register"
status: "Draft"
owner: Pasindu Dilshan
updated: 2026-11-12
---

# Requirements Register

Status values: Draft (written, not confirmed), Confirmed (business owner agreed), Built, Verified, Rejected.

## R1: Leave balancing

| ID | Title | Status | Owner to confirm |
| --- | --- | --- | --- |
| LV-001 | Leave types | Confirmed | HR |
| LV-002 | Leave period is the calendar year | Confirmed | HR |
| LV-003 | Casual leave before the 1-year mark | Built | HR |
| LV-004 | Casual leave after the 1-year mark | Built | HR |
| LV-005 | Additional leave before the 1-year mark | Built | HR |
| LV-006 | Annual leave by quarter of the 1-year mark | Verified | HR |
| LV-007 | Medical leave | Confirmed | HR, Management |
| LV-008 | Leave balance calculation | Confirmed | HR |
| LV-009 | Application and approval flow | Confirmed | HR |
| LV-010 | Low and critical balance alerts | Built | HR |
| LV-011 | Rules configurable per customer | Confirmed | Product owner |
| LV-012 | Company and branch isolation | Confirmed | Product owner |
| LV-013 | Migration from the leave Sheet | Confirmed | HR |
| LV-014 | Holiday calendar and Saturday half days | Confirmed | HR |

Details and acceptance criteria: [leave-rules.md](leave-rules.md).

LV-006 confirmed 2026-11-11 and the other R1 leave rules confirmed 2026-11-12 by the product owner, following the current leave Sheet policy; sources for each answer are in leave-rules.md and open-questions.md. LV-007: the medical allocation is built; routing medical applications to the management approver waits for Q23, so the requirement stays Confirmed.

## Later releases (not started)

| Epic | Prefix | Release |
| --- | --- | --- |
| Attendance: devices, office-network check-in, GPS check-in | AT | R2 |
| Payroll: Sri Lanka EPF, ETF, APIT, payslips, bank file | PY | R2 |
| Assets, insurance, items issued to staff | AS | R3 |
| Renewals and reminders | RN | R3 |
| IT helpdesk and network register | IT | R3 |
| Petty cash, cheque collection ledger, utility bills | FN | R4 |

## Non-functional

| ID | Requirement | Status |
| --- | --- | --- |
| NFR-SEC-001 | OWASP ASVS 5.0 Level 2 controls for custom code | Draft |
| NFR-SEC-002 | Two-factor login for admin, HR and Finance roles | Draft |
| NFR-SEC-003 | PDPA duties met before 2027-01-01 | Draft |
| NFR-REL-001 | RPO 24 h and RTO 4 h at R1; RPO 1 h from payroll go-live | Draft |
| NFR-PERF-001 | Lists and reports respond in under 2 s for 100 concurrent users on staging | Draft |
| NFR-BRD-001 | Every user-facing name, logo and email footer comes from the site's branding settings (ADR-0006) | Draft |
| NFR-AUD-001 | Every change to leave, payroll and money records is traceable to a user and time | Draft |
