---
title: "Monitoring"
status: "Draft"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Monitoring

| Signal | Tool | Alert when |
| --- | --- | --- |
| Uptime | External uptime checker on the login page | Down for 2 checks |
| Errors | Frappe Error Log; optional Sentry-compatible tracker | New error type, or more than 10 in 10 minutes |
| Scheduled jobs | Scheduled Job Log | Annual allocation or reminders job failed |
| Server | Host metrics (CPU, memory, disk) | CPU > 80% for 15 min; disk > 80% |
| Database | Slow query log | Query > 2 s repeatedly |
| Security | Failed logins, System Manager changes, new API keys | Spikes or any change outside a release |
| Backups | Backup job status | Missed or failed backup |

Alerts go to the engineer and the second admin. Scaling stages are triggered by these signals (see the Master Plan, Security and operations tab).
