---
title: "Testing Standards"
status: "Approved"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Testing Standards

## Levels

| Level | What | Where | Runs |
| --- | --- | --- | --- |
| Unit | Service functions with plain inputs (dates, settings values) | `services/test_*.py` | Every commit |
| Integration | DocType lifecycle, permissions, scheduler jobs, API endpoints on a test site | `doctype/*/test_*.py` | Every pull request |
| Reconciliation | New system figures against the legacy source (Sheet, old ERP) | `docs/testing/evidence/` | Before each go-live |
| Security | Role and company isolation, input validation, scans | CI + manual review | Every pull request / release |
| Performance | Realistic data volumes on staging | k6 or equivalent | Before ERP-stage go-live |

## Rules
- Write tests before implementing a business rule.
- Each requirement's acceptance criteria map to named tests; record them in the traceability matrix.
- Cover: valid case, boundaries (quarter edges, 31 Mar / 1 Apr), invalid input, wrong role, other company's data, duplicate run, cancellation.
- Test data is synthetic. Never copy real employee names, NIC numbers, salaries or contacts into tests or fixtures.
- Tests are independent and repeatable; they create and clean their own records.
- A failing test is investigated and reported. Tests are never weakened to pass.

## Commands

```bash
bench --site test.localhost run-tests --app nortix
bench --site test.localhost run-tests --app nortix --module nortix.hr_leave.services.test_annual
```

## Evidence
CI logs and reconciliation results for each release are stored or linked under `docs/testing/evidence/`.
