---
title: "Python and Frappe Coding Standards"
status: "Approved"
owner: Pasindu Dilshan
updated: 2026-11-09
---

# Python and Frappe Coding Standards

## Tooling
- Formatter and linter: `ruff` (configured by `bench new-app`; run through pre-commit).
- Indentation: tabs, as in the Frappe codebase.
- Python version: the version required by the installed Frappe major release.

## Structure inside the app

```text
nortix/
  hr_leave/                 one module per business area
    doctype/                DocTypes (JSON + controller + test)
    services/               business rules as plain functions
    report/                 script reports
    api.py                  whitelisted endpoints for this module
  localisation/lk/          country rules (EPF, ETF, APIT)
  patches/                  data migrations, listed in patches.txt
  fixtures/                 roles, custom fields, workspaces exported as fixtures
  hooks.py
```

## Naming
- Modules: snake_case business areas (`hr_leave`, `admin_assets`, `finance_office`).
- DocTypes: Title Case, singular (`Issued Item`, `Renewal`, `Nortix Leave Settings`).
- Fields: snake_case nouns (`confirmation_date`, `annual_allocation_days`).
- Functions: verbs (`allocate_annual_leave`, `get_quarter_entitlement`).
- Constants: UPPER_SNAKE only for true constants, never for customer values.

## Rules
- Controllers stay thin: `validate`, `on_submit`, `on_cancel` call service functions.
- Service functions take explicit arguments and return values; no hidden global state.
- Use `frappe.qb` or `frappe.get_all` with filters. Never build SQL with string formatting or f-strings.
- Every `@frappe.whitelist()` endpoint checks permissions (`frappe.has_permission` or `doc.check_permission`) and validates input types.
- Use `frappe.throw` with translatable messages (`_("...")`) for business errors; never expose stack traces to users.
- Dates: `frappe.utils.getdate`, `add_months`, `date_diff`; never naive string parsing.
- Money and leave days: `flt` with explicit precision; compare with tolerance where fractional.
- Scheduled jobs are idempotent: check for an existing record before creating one.
- Long work runs in `frappe.enqueue`, not in a request.
- Log with `frappe.logger("nortix")`; never log personal data or secrets.

## Comments and docstrings
- Public service functions have a one-line docstring stating what they return and the requirement ID.
- Comments explain why a rule exists or why an approach was chosen. Do not restate the code.
- Reference requirement IDs where a rule is implemented: `# LV-006: quarter of the 1-year mark sets the first-year amount.`
- No commented-out code, no TODO without an issue reference, no tool or assistant references.

## Example

```python
def get_quarter_entitlement(mark_date, period_year, settings):
	"""Return first-year annual leave days for a 1-year mark (LV-006)."""
	if mark_date.year < period_year:
		return settings.annual_full_days
	quarter = (mark_date.month - 1) // 3 + 1
	return settings.get(f"annual_q{quarter}_days")
```
