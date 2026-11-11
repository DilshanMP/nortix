import frappe
from frappe.utils import today

from nortix.hr_leave.services.annual import allocate_due_annual_leave


def daily():
	"""Scheduler entry point. LV-006 allocations run only after HR switches them on, so the
	job cannot create allocations ahead of the leave Sheet import."""
	if not frappe.db.get_single_value("Nortix Leave Settings", "is_annual_allocation_enabled"):
		return
	allocate_due_annual_leave(today())
