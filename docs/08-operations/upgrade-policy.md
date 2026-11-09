---
title: "Upgrade Policy"
status: "Draft"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Upgrade Policy

| Type | When | Process |
| --- | --- | --- |
| Security patch (Frappe, ERPNext, HRMS, OS) | Within 7 days of release | Staging, smoke test, production |
| Minor update | Monthly | Staging, full test suite, production |
| Major version | Once a year, after the first point releases | Upgrade plan, staging copy of production, full regression and reconciliation, sign-off |

Before each major upgrade, review release notes for removed APIs used by `nortix` and update ADRs if behaviour changes.
