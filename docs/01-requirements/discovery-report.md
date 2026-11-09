---
title: "Discovery Report"
status: "Draft"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Discovery Report

## Confirmed facts
- About 60 staff; 57 in the leave Sheet's Employee Master; a few HR and accounts admins.
- Six companies, four branches (head office, service centre, two warehouses), seven employee departments in the Sheet.
- Leave rules as in `leave-rules.md` (Draft until HR confirms).
- Wanted modules: payroll, attendance devices over WiFi/IP, assets with insurance, items issued to staff, renewal reminders, IT and network, petty cash, cheques, utility bills; organised by department.
- The current ERP is about 20 years old and will be replaced by a web-based ERP.
- Platform decision approved 2026-11-09: Frappe HR + ERPNext + custom app (ADR-0001).
- The product must be usable by other companies (ADR-0002, ADR-0004).

## Assumptions
- One lead engineer builds with AI assistance; business owners review rules.
- Cloud hosting is acceptable (pending PDPA cross-border review).
- Fewer than 100 concurrent users until the ERP stage.

## Unknowns
See `open-questions.md`.

## Conflicts
- The Sheet lists six companies; the legacy ERP analysis notes four company systems.
- PostgreSQL is preferred in the master guide; ERPNext v16 supports MariaDB officially.
- IP ownership of a product built for the employer and offered to other companies is not yet agreed.
- The product name Nortix is also used by other companies, including a software and SaaS company (NortixLabs); trademark risk to be checked before public launch (D7).
