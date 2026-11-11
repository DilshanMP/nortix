import frappe
from frappe.utils import today

from nortix.hr_leave.services.annual import allocate_due_annual_leave
from nortix.hr_leave.services.balance_alerts import send_weekly_alerts
from nortix.hr_leave.services.leave_allocation_job import allocate_due_leave


def daily():
	"""Scheduler entry point. Each leave rule runs only after HR switches it on, so the jobs
	cannot create allocations ahead of the leave Sheet import."""
	if frappe.db.get_single_value("Nortix Leave Settings", "is_annual_allocation_enabled"):
		allocate_due_annual_leave(today())
	allocate_due_leave(today())


def weekly():
	"""Scheduler entry point for the LV-010 summary; it sends nothing unless switched on."""
	send_weekly_alerts(today())
