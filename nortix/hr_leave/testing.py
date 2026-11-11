"""Synthetic test data for the HR Leave module. Never put real names, contacts or IDs here."""

import frappe

ANNUAL_LEAVE_TYPE = "_Test Nortix Annual"
CASUAL_LEAVE_TYPE = "_Test Nortix Casual"
ADDITIONAL_LEAVE_TYPE = "_Test Nortix Additional"
MEDICAL_LEAVE_TYPE = "_Test Nortix Medical"
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


def set_leave_settings(**values) -> None:
	"""Turn on casual, additional and medical allocation with the leave Sheet amounts."""
	for leave_type in (CASUAL_LEAVE_TYPE, ADDITIONAL_LEAVE_TYPE, MEDICAL_LEAVE_TYPE):
		make_leave_type(leave_type)
	settings = frappe.get_single("Nortix Leave Settings")
	settings.update(
		{
			"is_casual_allocation_enabled": 1,
			"casual_leave_type": CASUAL_LEAVE_TYPE,
			"casual_monthly_days_first_year": 0.5,
			"casual_days_before_mark": 6,
			"casual_days_after_mark": 7,
			"is_additional_allocation_enabled": 1,
			"additional_leave_type": ADDITIONAL_LEAVE_TYPE,
			"additional_days_before_mark": 1,
			"is_medical_allocation_enabled": 1,
			"medical_leave_type": MEDICAL_LEAVE_TYPE,
			"medical_days": 7,
		}
	)
	settings.update(values)
	settings.save()


def make_holiday_list_for(company: str, abbr: str) -> str:
	"""A 2026 holiday list with no holidays, assigned to the company, so leave days count plainly."""
	from hrms.hr.doctype.holiday_list_assignment.test_holiday_list_assignment import (
		create_holiday_list_assignment,
	)

	holiday_list = f"_Test Nortix Holidays {abbr}"
	if not frappe.db.exists("Holiday List", holiday_list):
		frappe.get_doc(
			{
				"doctype": "Holiday List",
				"holiday_list_name": holiday_list,
				"from_date": "2026-01-01",
				"to_date": "2026-12-31",
			}
		).insert()
	create_holiday_list_assignment(
		"Company", company, holiday_list=holiday_list, company=company, from_date="2026-01-01"
	)
	return holiday_list


def take_leave(employee: str, company: str, leave_type: str, from_date: str, to_date: str, status="Approved"):
	doc = frappe.get_doc(
		{
			"doctype": "Leave Application",
			"employee": employee,
			"company": company,
			"leave_type": leave_type,
			"from_date": from_date,
			"to_date": to_date,
			"posting_date": from_date,
			"status": status,
		}
	).insert()
	if status == "Approved":
		doc.submit()
	return doc


def before_tests():
	"""Complete site setup before the nortix tests, as Frappe HR does for its own tests.

	Frappe runs only the tested app's before_tests hooks, so on a fresh CI site nothing else
	runs the setup wizard, and creating a company fails for want of ERPNext's base records
	(Warehouse Type "Transit", genders, the fiscal year)."""
	from hrms.tests.test_utils import before_tests as hrms_before_tests

	hrms_before_tests()
