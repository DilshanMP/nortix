from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

CUSTOM_FIELDS = {
	"Leave Allocation": [
		{
			"fieldname": "nortix_source",
			"label": "Allocation Source",
			"fieldtype": "Select",
			"options": "\nannual_rule\ncasual_rule\nadditional_rule\nmedical_rule\nmigration\nmanual",
			"insert_after": "leave_policy_assignment",
			"read_only": 1,
			"no_copy": 1,
			"in_standard_filter": 1,
			"description": "How the allocation was created: annual_rule, casual_rule, additional_rule or medical_rule by the daily leave jobs, migration by the leave Sheet import, manual by HR. Blank on allocations made in the form.",
		}
	],
	"Leave Adjustment": [
		{
			"fieldname": "nortix_source",
			"label": "Adjustment Source",
			"fieldtype": "Select",
			"options": "\ncasual_rule",
			"insert_after": "reason_for_adjustment",
			"read_only": 1,
			"no_copy": 1,
			"description": "casual_rule when the daily leave job added the casual day at the 1-year mark; blank for adjustments made by HR.",
		}
	],
}


def make_custom_fields():
	create_custom_fields(CUSTOM_FIELDS, update=True)


def after_install():
	make_custom_fields()


# Akvora's four leave types, as listed in the leave Sheet's Settings tab (LV-001). Annual and
# medical leave can hold more days than remain in a period (a late mark or a December joiner),
# so they allow over allocation; none carries forward (Q2) or is earned monthly.
LEAVE_TYPES = {
	"Casual Leave": {"allow_over_allocation": 0},
	"Additional Leave": {"allow_over_allocation": 0},
	"Annual Leave": {"allow_over_allocation": 1},
	"Medical Leave": {"allow_over_allocation": 1},
}
SETTINGS_FIELDS = {
	"Casual Leave": "casual_leave_type",
	"Additional Leave": "additional_leave_type",
	"Annual Leave": "annual_leave_type",
	"Medical Leave": "medical_leave_type",
}


def setup_leave_types() -> list[str]:
	"""LV-001: create or correct the four leave types and link them in Nortix Leave Settings.
	Automatic allocation stays switched off. Safe to run again. Returns the types created."""
	import frappe

	created = []
	for name, values in LEAVE_TYPES.items():
		flags = {"is_carry_forward": 0, "is_earned_leave": 0, "include_holiday": 0, **values}
		if frappe.db.exists("Leave Type", name):
			frappe.db.set_value("Leave Type", name, flags)
		else:
			frappe.get_doc({"doctype": "Leave Type", "leave_type_name": name, **flags}).insert()
			created.append(name)
	settings = frappe.get_single("Nortix Leave Settings")
	for name, fieldname in SETTINGS_FIELDS.items():
		if not settings.get(fieldname):
			settings.set(fieldname, name)
	settings.save()
	return created


def check_app_permission() -> bool:
	"""Show the Nortix tile on the apps screen to HR and system managers only."""
	import frappe

	if frappe.session.user == "Administrator":
		return True
	return bool(set(frappe.get_roles()) & {"HR Manager", "HR User", "System Manager"})
