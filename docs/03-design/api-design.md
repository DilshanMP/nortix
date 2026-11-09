---
title: "API Design"
status: "Approved"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# API Design

## Standard API
Frappe exposes every DocType at `/api/resource/<DocType>` (v1) and `/api/v2/document/<DocType>` where available; these apply role and user permissions. Prefer them for simple CRUD by integrations.

## Custom endpoints
- Live in `<module>/api.py`, decorated with `@frappe.whitelist()`.
- Accept explicit, typed arguments; validate every argument.
- Check permission first (`frappe.has_permission(doctype, ptype, doc)`).
- Return plain JSON-serialisable dicts; never return whole documents with hidden fields.
- Never `allow_guest=True` except for documented public endpoints (none planned).
- Name by action: `get_leave_summary`, `submit_device_punches`.

## Integration users
One user per integration, API key and secret, minimum roles, User Permissions on Company. Keys are rotated yearly and on staff exit.

## Versioning and contracts
- Breaking changes need a new endpoint name or version and a deprecation note in `CHANGELOG.md`.
- Each custom endpoint is documented in `docs/02-architecture/integration.md` with request, response and errors.

## Errors
Business errors use `frappe.throw` with a clear message and HTTP 417 (Frappe default for validation); permission errors return 403. No stack traces to clients.

## Rate limiting
Use Frappe's `rate_limit` decorator on custom endpoints that can be abused (check-in, login-adjacent actions).
