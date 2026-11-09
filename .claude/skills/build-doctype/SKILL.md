---
name: build-doctype
description: "Design and create a custom Frappe DocType that follows project conventions (company field, permissions, naming, track changes, tests). Use when a requirement needs a new record type."
argument-hint: "<DocType name> <module>"
---

# Build a DocType

1. Confirm a standard DocType cannot be reused or extended with custom fields.
2. Draft the field table (name, label, type, mandatory, permlevel, description) and add it to the module's data dictionary in `docs/04-data/`.
3. Apply docs/03-design/doctype-conventions.md: Title Case name, naming series, mandatory `company`, track changes, submittable when it affects balances or money, permissions per role.
4. Create it with `bench --site dev.localhost new-doctype` or the DocType form in developer mode so JSON lands in the app.
5. Keep the controller thin; put logic in `services/`.
6. Add `test_<doctype>.py` with permission and company-isolation tests.
