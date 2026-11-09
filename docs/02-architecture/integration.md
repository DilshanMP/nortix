---
title: "Integration Design"
status: "Draft"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Integration Design

| Integration | Direction | Method | Auth | Idempotency | Release |
| --- | --- | --- | --- | --- | --- |
| Attendance devices (pull) | In | Sync tool reads device by IP:4370, posts Employee Checkin | API key of an integration user with only checkin rights | Device ID + timestamp unique | R2 |
| Attendance devices (push, ADMS) | In | Device posts to a connector endpoint | Device serial allow-list + secret | Same key | R2 |
| Phone check-in (office network) | In | Frappe HR app; server checks request IP against office IP list in settings | User session | One checkin per log type per minute | R2 |
| Email / SMS | Out | Frappe Email Account; SMS gateway | Provider credentials in site config | Message queue | R1 |
| Bank salary file | Out | Export file in bank format | Finance role | File per payroll entry | R2 |
| EPF / ETF / APIT returns | Out | Export files | Finance role | Per period | R2 |
| Legacy ERP | Both | CSV exchange first; REST later | Integration user | Batch ID | ERP stage |

## Rules
- Every integration uses its own integration user with the minimum roles.
- API keys and secrets live in site config or the secret store, never in Git.
- Webhooks are signed (HMAC) and verified.
- Failed messages are logged with a reason and retried; nothing is silently dropped.
- Every inbound integration has a reconciliation report.
