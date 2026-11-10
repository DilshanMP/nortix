"""Guard for the `nortix_source` audit field on Leave Allocation (LV-006, LV-013)."""

from contextlib import contextmanager

import frappe
from frappe import _

FLAG = "nortix_allow_allocation_source"


@contextmanager
def allow_allocation_source():
	"""Let server code (the annual job, the Sheet import) record how an allocation was created."""
	previous = frappe.flags.get(FLAG)
	frappe.flags[FLAG] = True
	try:
		yield
	finally:
		frappe.flags[FLAG] = previous


def validate_allocation_source(doc, method=None) -> None:
	"""Reject `nortix_source` set from a form or the API.

	The field is trusted: the annual job skips an employee whose cancelled allocation is marked
	`annual_rule`, so a user who could set it could silently block that employee's leave or
	disguise a manual allocation as automatic.
	"""
	if not doc.get("nortix_source") or frappe.flags.get(FLAG):
		return
	if doc.is_new() or doc.has_value_changed("nortix_source"):
		frappe.throw(
			_("Allocation Source is set by the system and cannot be entered."),
			frappe.PermissionError,
			title=_("Not Allowed"),
		)
