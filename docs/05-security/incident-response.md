---
title: "Incident Response"
status: "Draft"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Incident Response

## Roles
| Role | Person |
| --- | --- |
| Incident lead | Pasindu Dilshan |
| Second admin | To be named (D6) |
| Management contact | To be named |
| Hosting support | Provider support channel |

## Severity
| Level | Example | Response |
| --- | --- | --- |
| S1 | Data breach, site down, wrong payroll posted | Immediately; management informed within 1 hour |
| S2 | Feature broken for a department | Same working day |
| S3 | Minor defect | Next planned release |

## Steps
1. **Detect and record:** time, reporter, symptoms, affected sites.
2. **Contain:** disable affected accounts or integrations; enable maintenance mode if needed.
3. **Preserve evidence:** keep logs and a backup snapshot before changes.
4. **Recover:** fix forward or restore from backup per `docs/08-operations/backup-restore.md`.
5. **Notify:** management; affected staff; the Data Protection Authority where the PDPA requires.
6. **Review:** within 5 working days write a post-incident note in `docs/08-operations/incidents/` with cause, impact, fixes and prevention.
