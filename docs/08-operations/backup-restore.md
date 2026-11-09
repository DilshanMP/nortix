---
title: "Backup and Restore"
status: "Draft"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Backup and Restore

| Item | Target (to approve, D5) |
| --- | --- |
| RPO | 24 h at R1; 1 h from payroll go-live |
| RTO | 4 h |
| Frequency | Daily full (database + files); more often from payroll go-live |
| Location | Offsite, encrypted, one copy production cannot delete |
| Retention | 30 daily, 12 monthly |
| Restore drill | Monthly on staging, timed, recorded below |

## Restore steps (own server)
```bash
bench --site <staging-site> restore <database.sql.gz> --with-public-files <public.tar> --with-private-files <private.tar>
bench --site <staging-site> migrate
```
Verify: login, record counts for Employee, Leave Application, Leave Allocation match the backup's source.

## Drill log
| Date | Backup used | Time to restore | Result | By |
| --- | --- | --- | --- | --- |
