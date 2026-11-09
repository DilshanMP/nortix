---
title: "Secure Coding Rules (Frappe)"
status: "Approved"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Secure Coding Rules (Frappe)

1. `@frappe.whitelist()` methods check permission before reading or writing: `frappe.has_permission(doctype, "write", doc, throw=True)`.
2. Never `ignore_permissions=True` in code reachable from a request, unless the method has already checked a stricter condition; comment the reason with the requirement ID.
3. No `frappe.db.sql` with f-strings, `%` formatting or concatenation; use `frappe.qb`, `frappe.get_all` with filters, or parameterised `frappe.db.sql(query, values)`.
4. No `allow_guest=True`.
5. Validate argument types (`frappe.utils.cint`, `flt`, `getdate`) and ranges.
6. Secrets in `site_config.json` or environment, read with `frappe.conf`; never in code, fixtures or Git.
7. Do not log personal data, tokens or full request bodies.
8. Use `frappe.throw(_("..."))` for user errors; never expose exception text.
9. Files from users are private (`is_private=1`) unless they must be public.
10. Every integration endpoint verifies its signature or API key and is rate limited.
11. Dependencies are added only with approval and must pass `pip-audit` / `npm audit` in CI.
