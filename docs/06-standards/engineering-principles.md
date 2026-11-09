---
title: "Engineering Principles"
status: "Approved"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Engineering Principles

These principles decide trade-offs when no specific rule applies.

1. **Correctness first.** A wrong leave balance, payslip or ledger entry costs more than a late feature. When speed and correctness conflict, correctness wins.
2. **Simplest architecture that meets proven requirements.** A modular monolith on one platform. Add services, queues or replicas only when a measurement shows the need.
3. **Configuration over code.** Rules that differ between customers (leave amounts, approval levels, statutory rates) live in settings DocTypes. Code reads settings; it never contains a customer's numbers.
4. **Platform first, custom second.** Use a standard Frappe/ERPNext feature before writing a custom one. Extend through hooks, custom fields and the `nortix` app; never edit core apps.
5. **Thin controllers, tested services.** Business rules live in plain Python functions under `services/`, tested without the UI. DocType controllers and API endpoints only orchestrate.
6. **Server-side truth.** Validation and permission checks run on the server for every path: form, API, import, scheduler.
7. **Immutable money and leave history.** Submitted documents are cancelled and amended, never edited. Corrections are new documents with a reason.
8. **Idempotent automation.** Every scheduled job and integration can run twice without creating duplicates.
9. **Isolation by design.** Every transactional record carries its Company; access is limited by User Permissions. One site per customer organisation.
10. **Traceable change.** Every change links to a requirement or ADR, passes CI and is reviewed before merge.
11. **Evidence over claims.** Tests, scans and reconciliations count only when their real output is recorded.
12. **Leave it clearer.** Each change improves naming, tests or docs it touches; no unrelated refactors in feature pull requests.
