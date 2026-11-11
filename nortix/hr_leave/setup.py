from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

CUSTOM_FIELDS = {
	"Leave Allocation": [
		{
			"fieldname": "nortix_source",
			"label": "Allocation Source",
			"fieldtype": "Select",
			"options": "\nannual_rule\nmigration\nmanual",
			"insert_after": "leave_policy_assignment",
			"read_only": 1,
			"no_copy": 1,
			"in_standard_filter": 1,
			"description": "How the allocation was created: annual_rule by the daily annual leave job, migration by the leave Sheet import, manual by HR. Blank on allocations made in the form.",
		}
	]
}


def make_custom_fields():
	create_custom_fields(CUSTOM_FIELDS, update=True)


def after_install():
	make_custom_fields()
