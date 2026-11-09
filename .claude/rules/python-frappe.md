---
paths:
  - "nortix/**/*.py"
---

# Python and Frappe rules

- Follow docs/06-standards/coding-standards-python.md and docs/05-security/secure-coding.md.
- Business rules go in `services/`; controllers and `api.py` only orchestrate.
- Read customer values from settings DocTypes; never hard-code them.
- Every whitelisted method checks permission first and validates argument types.
- Use `frappe.qb` or `frappe.get_all`; no SQL built from strings.
- Scheduled jobs and imports are idempotent.
- Tabs for indentation. Docstring on public service functions with the requirement ID.
- Comments explain why; no narration, no tool references.
