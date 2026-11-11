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
