from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from nortix.hr_leave import tasks
from nortix.hr_leave.services.calendar import build_calendar, holiday_list_name
from nortix.hr_leave.testing import (
	CASUAL_LEAVE_TYPE,
	COMPANY_A,
	make_company,
	make_employee,
	make_leave_period,
	make_leave_type,
	make_user,
	set_annual_settings,
	set_leave_settings,
	take_leave,
)

GET_DAYS = "hrms.hr.doctype.leave_application.leave_application.get_number_of_leave_days"


def save_holiday_year(year, holidays):
	name = frappe.db.get_value("Nortix Holiday Year", {"year": year})
	doc = frappe.get_doc("Nortix Holiday Year", name) if name else frappe.new_doc("Nortix Holiday Year")
	doc.year = year
	doc.set("holidays", [{"holiday_date": d, "description": text} for d, text in holidays])
	doc.save()
	return doc


def holiday_rows(year):
	return frappe.get_all(
		"Holiday",
		filters={"parent": holiday_list_name(year), "parenttype": "Holiday List"},
		fields=["holiday_date", "weekly_off", "is_half_day", "description"],
		order_by="holiday_date",
	)


def assignments(year):
	return frappe.get_all(
		"Holiday List Assignment",
		filters={"holiday_list": holiday_list_name(year), "docstatus": 1, "applicable_for": "Company"},
		pluck="assigned_to",
	)


def allocate(employee, days):
	doc = frappe.get_doc(
		{
			"doctype": "Leave Allocation",
			"employee": employee,
			"company": COMPANY_A,
			"leave_type": CASUAL_LEAVE_TYPE,
			"from_date": "2026-01-01",
			"to_date": "2026-12-31",
			"new_leaves_allocated": days,
		}
	).insert()
	doc.submit()


class TestCalendarBuild(IntegrationTestCase):
	"""LV-014: the yearly calendar, its company assignments and Saturday half-day leave counts."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		make_company(COMPANY_A, "_TNA")
		make_leave_period(COMPANY_A)
		make_leave_type()
		set_annual_settings(is_annual_allocation_enabled=0)
		set_leave_settings(
			is_casual_allocation_enabled=0,
			is_additional_allocation_enabled=0,
			is_medical_allocation_enabled=0,
		)

	def setUp(self):
		frappe.db.savepoint("nortix_calendar_test")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback(save_point="nortix_calendar_test")

	def test_saving_holidays_builds_calendar_once(self):
		save_holiday_year(2026, [("2026-03-03", "Test Holiday")])
		first = holiday_rows(2026)
		save_holiday_year(2026, [("2026-03-03", "Test Holiday")])
		self.assertEqual(holiday_rows(2026), first)
		self.assertEqual(len(first), 105)
		[holiday] = [row for row in first if str(row.holiday_date) == "2026-03-03"]
		self.assertEqual((holiday.weekly_off, holiday.is_half_day), (0, 0))

	def test_added_and_removed_holidays_are_reflected(self):
		save_holiday_year(2026, [("2026-03-03", "Test Holiday")])
		save_holiday_year(2026, [("2026-04-14", "Other Holiday")])
		dates = {str(row.holiday_date) for row in holiday_rows(2026)}
		self.assertIn("2026-04-14", dates)
		self.assertNotIn("2026-03-03", dates)

	def test_one_assignment_per_company(self):
		save_holiday_year(2026, [])
		build_calendar(2026)
		assigned = assignments(2026)
		self.assertIn(COMPANY_A, assigned)
		self.assertEqual(len(assigned), len(set(assigned)))

	def test_company_with_another_calendar_is_reported_not_replaced(self):
		other_list = "_Test Nortix Other Calendar"
		if not frappe.db.exists("Holiday List", other_list):
			frappe.get_doc(
				{
					"doctype": "Holiday List",
					"holiday_list_name": other_list,
					"from_date": "2026-01-01",
					"to_date": "2026-12-31",
				}
			).insert()
		make_company("_Test Nortix Company E", "_TNE")
		existing = frappe.get_doc(
			{
				"doctype": "Holiday List Assignment",
				"applicable_for": "Company",
				"assigned_to": "_Test Nortix Company E",
				"holiday_list": other_list,
				"from_date": "2026-01-01",
			}
		).insert()
		existing.submit()
		logs_before = frappe.db.count("Error Log", {"method": "Holiday calendar needs review"})
		save_holiday_year(2026, [])
		self.assertNotIn("_Test Nortix Company E", assignments(2026))
		self.assertEqual(frappe.db.get_value("Holiday List Assignment", existing.name, "docstatus"), 1)
		self.assertGreater(
			frappe.db.count("Error Log", {"method": "Holiday calendar needs review"}), logs_before
		)

	def test_new_company_is_assigned_on_next_build(self):
		save_holiday_year(2026, [])
		make_company("_Test Nortix Company D", "_TND")
		build_calendar(2026)
		self.assertIn("_Test Nortix Company D", assignments(2026))

	def test_friday_and_saturday_count_one_and_a_half(self):
		save_holiday_year(2026, [])
		employee = make_employee(COMPANY_A, "2024-01-01")
		allocate(employee, 6)
		application = take_leave(employee, COMPANY_A, CASUAL_LEAVE_TYPE, "2026-03-06", "2026-03-07")
		self.assertEqual(application.total_leave_days, 1.5)
		ledger = frappe.get_all(
			"Leave Ledger Entry",
			filters={"transaction_name": application.name, "docstatus": 1},
			pluck="leaves",
		)
		self.assertEqual(ledger, [-1.5])

	def test_full_week_and_half_day_saturday(self):
		save_holiday_year(2026, [])
		employee = make_employee(COMPANY_A, "2024-01-02")
		allocate(employee, 6)
		week = take_leave(employee, COMPANY_A, CASUAL_LEAVE_TYPE, "2026-03-09", "2026-03-15")
		self.assertEqual(week.total_leave_days, 5.5)
		half = frappe.get_doc(
			{
				"doctype": "Leave Application",
				"employee": employee,
				"company": COMPANY_A,
				"leave_type": CASUAL_LEAVE_TYPE,
				"from_date": "2026-03-21",
				"to_date": "2026-03-21",
				"half_day": 1,
				"half_day_date": "2026-03-21",
				"posting_date": "2026-03-21",
				"status": "Open",
			}
		).insert()
		self.assertEqual(half.total_leave_days, 0.5)

	def test_balance_check_uses_corrected_days(self):
		save_holiday_year(2026, [])
		enough = make_employee(COMPANY_A, "2024-01-03")
		short = make_employee(COMPANY_A, "2024-01-03")
		allocate(enough, 1.5)
		allocate(short, 1)
		take_leave(enough, COMPANY_A, CASUAL_LEAVE_TYPE, "2026-03-06", "2026-03-07")
		with self.assertRaisesRegex(frappe.ValidationError, "(?i)insufficient"):
			take_leave(short, COMPANY_A, CASUAL_LEAVE_TYPE, "2026-03-06", "2026-03-07")

	def test_form_api_returns_corrected_days(self):
		save_holiday_year(2026, [])
		employee = make_employee(COMPANY_A, "2024-01-04")
		method = frappe.get_attr(frappe.override_whitelisted_method(GET_DAYS))
		self.assertEqual(method(employee, CASUAL_LEAVE_TYPE, "2026-03-06", "2026-03-07"), 1.5)

	def test_employee_cannot_edit_holiday_year(self):
		save_holiday_year(2026, [])
		frappe.set_user(make_user("nortix.calendar.employee@example.com", ["Employee"]))
		with self.assertRaises(frappe.PermissionError):
			save_holiday_year(2026, [("2026-05-01", "Not Allowed")])

	def test_daily_job_creates_next_year_from_december_once(self):
		with patch("nortix.hr_leave.tasks.today", return_value="2026-11-30"):
			tasks.daily()
		self.assertFalse(frappe.db.exists("Holiday List", holiday_list_name(2027)))
		with patch("nortix.hr_leave.tasks.today", return_value="2026-12-01"):
			tasks.daily()
			tasks.daily()
		self.assertTrue(frappe.db.exists("Holiday List", holiday_list_name(2027)))
		self.assertEqual(frappe.db.count("Nortix Holiday Year", {"year": 2027}), 1)
		self.assertEqual(len(holiday_rows(2027)), 104)
