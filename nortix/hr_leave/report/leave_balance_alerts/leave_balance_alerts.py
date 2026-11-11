import frappe
from frappe import _

from nortix.hr_leave.services.balance_alerts import get_balance_alerts


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = [
		{
			"label": _("Employee"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 140,
		},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
		{
			"label": _("Company"),
			"fieldname": "company",
			"fieldtype": "Link",
			"options": "Company",
			"width": 180,
		},
		{
			"label": _("Leave Type"),
			"fieldname": "leave_type",
			"fieldtype": "Link",
			"options": "Leave Type",
			"width": 140,
		},
		{"label": _("Balance"), "fieldname": "balance", "fieldtype": "Float", "width": 90},
		{"label": _("Level"), "fieldname": "level", "fieldtype": "Data", "width": 90},
	]
	return columns, get_balance_alerts(filters.get("date"), company=filters.get("company"))
