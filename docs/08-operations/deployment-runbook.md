---
title: "Deployment Runbook"
status: "Draft"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Deployment Runbook

## Before
- [ ] Release checklist complete (`docs/09-delivery/release-checklist.md`)
- [ ] Tag created (`vX.Y.Z`) and CHANGELOG updated
- [ ] Fresh backup of the production site taken and its size checked
- [ ] Maintenance window agreed with users if migrations run

## Frappe Cloud
1. Push the tag to GitHub.
2. In the bench group, deploy the new app version; review the patch list.
3. Update the staging site first; run smoke tests.
4. Update the production site.

## Own server
```bash
cd ~/frappe-bench
bench --site <site> backup --with-files
bench update --apps nortix --pull   # or: cd apps/nortix && git fetch && git checkout vX.Y.Z
bench --site <site> migrate
bench build --app nortix
sudo supervisorctl restart all
```

## After
- [ ] Smoke test: login, leave application, approval, balance report
- [ ] Error log empty of new errors for 30 minutes
- [ ] Release note sent to users

## Rollback
1. Maintenance mode on.
2. Restore the pre-deployment backup (see `backup-restore.md`).
3. Check out the previous tag and run `bench build`.
4. Record the incident.
