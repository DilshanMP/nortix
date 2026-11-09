---
title: "Environments"
status: "Approved"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Environments

| Environment | Where | Data | Who | Purpose |
| --- | --- | --- | --- | --- |
| Development | Engineer's machine (WSL2 or Docker) | Synthetic only | Engineer | Build and unit/integration tests (`dev.localhost`, `test.localhost`) |
| Staging | Same hosting as production, separate site | Copy of production, access restricted | Engineer, business testers | UAT, reconciliation, restore drills, load tests |
| Production | Managed hosting (Frappe Cloud) or own server | Live | Users; admin by two named people | Live use |

Rules:
- Code moves only Development → Git → CI → Staging → Production.
- Staging data is handled as production data (same access rules).
- No direct changes on production; configuration changes are exported as fixtures or recorded in the change log.
