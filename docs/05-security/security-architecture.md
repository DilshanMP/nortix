---
title: "Security Architecture"
status: "Approved"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Security Architecture

No system can be guaranteed 100% secure. The aim is to lower the likelihood and impact of attacks, detect them, contain them and recover. Controls are layered so one failure does not expose data.

## Layers

| Layer | Controls |
| --- | --- |
| Edge | Cloudflare: DNS, TLS, DDoS protection, WAF managed rules, rate limiting on login paths |
| Host | Hardened OS (CIS baseline), only 80/443 public, SSH by key from allow-listed IPs, automatic security updates, database and Redis bound to private interfaces |
| Transport | HTTPS end to end (Cloudflare to origin certificate); HSTS |
| Identity | Frappe login with strong password policy; 2FA for admin, HR, Finance; account disabled on exit; no shared accounts |
| Authorisation | Roles per workspace; User Permissions on Company and Branch; permlevels for sensitive fields; server-side checks in every endpoint |
| Application | Input validation, ORM / query builder only, output escaping by framework, CSRF protection, rate limits on custom endpoints, safe error messages |
| Data | Classification (see `docs/04-data/data-classification.md`); encrypted Password fields; encrypted backups; no personal data in logs |
| Integrations | One integration user each with minimum roles; API keys rotated; signed webhooks |
| Supply chain | Pinned versions; dependency, secret and static scans in CI; only reviewed apps installed |
| Monitoring | Access and error logs, failed-login alerts, admin change alerts, uptime checks |
| Recovery | Daily encrypted offsite backups, monthly restore drill, incident runbook |

## Roles (R1)

| Role | Can |
| --- | --- |
| Employee | Apply for own leave, view own balance and payslips |
| Leave Approver | Approve leave for direct reports |
| HR User | Manage leave for assigned companies and branches |
| HR Manager | Settings, policies, migration, all HR reports for assigned companies |
| System Manager | Platform configuration; held by two named people only |

Separation of duties: the person who configures payroll settings is not the only approver of a payroll run.

## Reference standards
OWASP ASVS 5.0 (Level 2 target), OWASP Top 10:2025, NIST SSDF (SP 800-218 v1.1), CIS Benchmarks, Sri Lanka PDPA No. 9 of 2022. Verify current versions before each annual review.
