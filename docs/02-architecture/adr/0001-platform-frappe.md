---
title: "ADR-0001 Platform: Frappe Framework, Frappe HR and ERPNext"
status: "Approved"
owner: Pasindu Dilshan
date: 2026-11-09
approvers: Pasindu Dilshan
---

# ADR-0001: Platform: Frappe Framework, Frappe HR and ERPNext

## Context
Low budget, one lead engineer working with AI assistance, six companies, HR and office modules needed now, full ERP later. Payroll, accounting and audit must be correct from day one.

## Options considered
| Option | Weighted score (1–5) | Main reason |
| --- | --- | --- |
| A. Frappe HR + ERPNext + custom app | 4.00 | Tested payroll, accounting, stock and audit; no licence fees |
| B. Laravel + PostgreSQL custom | 2.95 | Every business module built from zero |
| C. Odoo Community + custom modules | 3.45 | Payroll and biometric attendance only in Enterprise |
| D. ASP.NET Core + SQL Server custom | 3.20 | Every module built from zero; licence costs |
| Spring Boot custom (discussed later) | about 3.0 | Same build effort as B and D |

Weights: business fit 20, security 20, maintainability 15, reliability 15, team 10, performance 10, cost 10.

## Decision
Build on Frappe Framework v16 with Frappe HR and ERPNext. All custom work in one app.

## Consequences
- Python and Frappe skills must be learned.
- MariaDB, not PostgreSQL, while ERPNext lacks official PostgreSQL support.
- Yearly major upgrades follow Frappe's cycle and are tested on staging.

## Review triggers
- ERP requirements analysis finds core processes ERPNext cannot meet without core changes.
- PostgreSQL becomes mandatory.
- No one can maintain Frappe long term.
- Mobile needs exceed a PWA.

## Sources
Master Plan (Technology research tab), accessed 2026-11-04 to 2026-11-09.
