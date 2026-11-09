---
title: "Architecture Overview"
status: "Approved"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Architecture Overview

Nortix is a modular monolith: one Frappe application server per deployment, one database per customer site, and one custom app (`nortix`) on top of Frappe HR and ERPNext. Outside systems connect only through the REST API.

## Context (C4 level 1)

```mermaid
C4Context
  title Nortix: system context
  Person(staff, "All staff", "Leave, check-in, payslips on the phone")
  Person(dept, "Department users", "HR, Finance, Admin and IT, Logistics, Sales")
  Person(mgmt, "Management", "Approvals, cross-company reports")
  System(nortix, "Nortix", "Frappe HR + ERPNext + nortix app")
  System_Ext(devices, "Attendance devices", "Punches by IP pull or ADMS push")
  System_Ext(legacy, "Legacy ERP", "Feeds until replaced")
  System_Ext(mail, "Email / SMS", "Reminders, payslips")
  System_Ext(bank, "Banks and statutory", "Salary, EPF/ETF, APIT files")
  Rel(staff, nortix, "Uses", "HTTPS")
  Rel(dept, nortix, "Uses", "HTTPS")
  Rel(mgmt, nortix, "Uses", "HTTPS")
  Rel(devices, nortix, "Sends punches", "REST")
  BiRel(legacy, nortix, "Exchanges files or API calls")
  Rel(nortix, mail, "Sends")
  Rel(nortix, bank, "Exports files")
```

## Containers (C4 level 2)

```mermaid
flowchart TB
  web[Office browser] --> cf
  pwa[Staff phone PWA /hrms] --> cf
  ext[Devices and systems: REST API, signed webhooks] --> cf
  cf[Cloudflare: DNS, TLS, DDoS, WAF] --> nginx
  subgraph server[Application server]
    nginx[Nginx reverse proxy] --> gunicorn[Web app: Gunicorn, Frappe, ERPNext, Frappe HR, nortix]
    nginx --> socket[Realtime: Socket.IO]
    workers[RQ workers and scheduler]
    redis[(Redis: cache, sessions, queue)]
    gunicorn --> redis
    workers --> redis
  end
  gunicorn --> db[(MariaDB: one database per site)]
  workers --> db
  gunicorn --> files[(File storage)]
  db --> backups[(Offsite encrypted backups)]
```

## Modules (C4 level 3, inside `nortix`)

| Module | Workspace | Builds on | Owns |
| --- | --- | --- | --- |
| `hr_leave` | HR | Frappe HR Leave | Leave settings, quarter allocation job, alerts, Sheet import |
| `hr_attendance` | HR | Employee Checkin | Office-network check-in rule, device sync config |
| `localisation/lk` | HR, Finance | Payroll | EPF, ETF, APIT components, return files |
| `admin_assets` | Admin and IT | ERPNext Asset | Issued Item register, exit checklist links |
| `admin_renewals` | Admin and IT, Finance | Notifications | Renewal register and reminders |
| `it_network` | Admin and IT | Helpdesk | Network device and IP register |
| `finance_office` | Finance | ERPNext Accounts | Petty cash, cheque and bill reports |
| `core` | All | Frappe | Roles, workspaces, shared utilities, settings |

Module rules: a module may call another module only through its `services` functions; no module reads another module's tables directly.

## Key decisions
See [adr/](adr/): platform (0001), site per customer (0002), no core edits (0003), configuration over code (0004), localisation module (0005), white-label branding (0006).
