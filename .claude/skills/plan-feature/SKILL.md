---
name: plan-feature
description: "Produce a scoped implementation plan for one approved requirement: files, DocTypes, services, tests, migration, permissions and rollback. Use in plan mode before any implementation."
argument-hint: "<requirement ID>"
---

# Plan a feature

Pre-condition: the requirement status is Confirmed. If not, stop and list what is missing.

1. Read the requirement, data dictionary, related DocTypes, services and tests.
2. Prefer standard Frappe/ERPNext behaviour; list what is truly custom.
3. Produce the plan:
   - Scope and out of scope
   - Files to add or change (paths)
   - Settings fields used (no hard-coded values)
   - Permissions and company isolation
   - Tests: names and what each proves (valid, boundary, invalid, wrong role, other company, duplicate run)
   - Patches or fixtures
   - Risks and rollback
   - Commit sequence (small commits in the order the work will be done)
4. Wait for approval. Do not edit files.
