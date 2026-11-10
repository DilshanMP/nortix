"""Synthetic test data for the HR Leave module. Never put real names, contacts or IDs here."""

import frappe

ANNUAL_LEAVE_TYPE = "_Test Nortix Annual"
COMPANY_A = "_Test Nortix Company A"
COMPANY_B = "_Test Nortix Company B"
COMPANY_NO_PERIOD = "_Test Nortix Company C"


def make_company(name: str, abbr: str) -> str:
	if not frappe.db.exists("Company", name):
		frappe.get_doc(
			{
				"doctype": "Company",
				"company_name": name,
				"abbr": abbr,
				"default_currency": "INR",
				"country": "India",
				"chart_of_accounts": "Standard",
			}
		).insert()
	return name


def make_leave_type(name: str = ANNUAL_LEAVE_TYPE, **values) -> str:
	if not frappe.db.exists("Leave Type", name):
		doc = frappe.get_doc({"doctype": "Leave Type", "leave_type_name": name, "allow_over_allocation": 1})
		doc.update(values)
		doc.insert()
	elif values:
		frappe.db.set_value("Leave Type", name, values)
	return name


def make_leave_period(
	company: str, from_date: str = "2026-01-01", to_date: str = "2026-12-31", is_active: int = 1
) -> str:
	existing = frappe.db.get_value(
		"Leave Period", {"company": company, "from_date": from_date, "to_date": to_date}, "name"
	)
	if existing:
		return existing
	return (
		frappe.get_doc(
			{
				"doctype": "Leave Period",
				"company": company,
				"from_date": from_date,
				"to_date": to_date,
				"is_active": is_active,
			}
		)
		.insert()
		.name
	)


def make_employee(
	company: str, date_of_joining: str, status: str = "Active", relieving_date: str | None = None
) -> str:
	doc = frappe.get_doc(
		{
			"doctype": "Employee",
			"first_name": "Test",
			"last_name": f"Employee {frappe.generate_hash(length=6)}",
			"company": company,
			"date_of_joining": date_of_joining,
			"date_of_birth": "1990-01-01",
			"gender": "Female",
			"status": "Active",
		}
	).insert()
	if status != "Active":
		doc.status = status
		if status == "Left":
			doc.relieving_date = relieving_date or date_of_joining
		doc.save()
	return doc.name


def make_user(email: str, roles: list[str], company: str | None = None) -> str:
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "Test",
				"send_welcome_email": 0,
				"roles": [{"role": role} for role in roles],
			}
		).insert()
	if company and not frappe.db.exists(
		"User Permission", {"user": email, "allow": "Company", "for_value": company}
	):
		frappe.get_doc(
			{"doctype": "User Permission", "user": email, "allow": "Company", "for_value": company}
		).insert()
	return email


def set_annual_settings(**values) -> None:
	settings = frappe.get_single("Nortix Leave Settings")
	settings.update(
		{
			"is_annual_allocation_enabled": 1,
			"annual_leave_type": ANNUAL_LEAVE_TYPE,
			"annual_q1_days": 14,
			"annual_q2_days": 10,
			"annual_q3_days": 7,
			"annual_q4_days": 4,
			"annual_full_days": 14,
		}
	)
	settings.update(values)
	settings.save()
