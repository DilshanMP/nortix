---
title: "JavaScript Coding Standards"
status: "Approved"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# JavaScript Coding Standards

## Tooling
- `eslint` and `prettier` from the `bench new-app` template, run through pre-commit.

## Form scripts (`doctype/*/*.js`)
- Keep them for UX only: field visibility, defaults, helpful messages, buttons.
- Never rely on client code for validation or permissions; the server repeats every check.
- Call the server with `frappe.call` to whitelisted methods; handle errors with `frappe.msgprint`.
- No business calculations that the server does not also perform.

## Vue / Frappe UI pages (if added later)
- Organise by business feature (`leave/`, `assets/`), not by file type.
- Keep server data, form state and URL filter state separate.
- Every list uses server-side paging and filtering.

## Style
- `const` by default, `let` when reassigned, never `var`.
- Small named functions; no anonymous logic blocks over 20 lines.
- User-facing strings wrapped in `__()` for translation.
- Comments follow the same rule as Python: explain why, never narrate.
