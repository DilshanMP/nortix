---
title: "Test Strategy"
status: "Approved"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Test Strategy

Testing follows `docs/06-standards/testing-standards.md`. For each release:

| Activity | R1 leave | R2 attendance, payroll | R3 admin, IT | R4 finance office |
| --- | --- | --- | --- | --- |
| Unit and integration | Yes | Yes | Yes | Yes |
| Isolation tests (company, role) | Yes | Yes | Yes | Yes |
| Reconciliation with legacy source | Leave Sheet balances | Two payroll months | Asset register | One month-end |
| Load test | Not needed | Before payroll go-live | Not needed | Before ERP stage |
| External security test | Not needed | Recommended | Not needed | Before ERP stage |

Evidence is stored under `docs/testing/evidence/<release>/` without personal data.
