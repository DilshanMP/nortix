from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from nortix.hr_leave.services.balance_alerts import get_balance_alerts, send_weekly_alerts
from nortix.hr_leave.testing import (
	ADDITIONAL_LEAVE_TYPE,
	ANNUAL_LEAVE_TYPE,
	CASUAL_LEAVE_TYPE,
	COMPANY_A,
	COMPANY_B,
	MEDICAL_LEAVE_TYPE,
	make_company,
	make_employee,
	make_holiday_list_for,
	make_leave_period,
	make_leave_type,
	make_user,
	set_annual_settings,
	set_leave_settings,
	take_leave,
)

ON_DATE = "2026-06-30"


def allocate(employee, company, leave_type, days):
	doc = frappe.get_doc(
		{
			"doctype": "Leave Allocation",
			"employee": employee,
			"company": company,
			"leave_type": leave_type,
			"from_date": "2026-01-01",
			"to_date": "2026-12-31",
			"new_leaves_allocated": days,
		}
	).insert()
	doc.submit()


def alert_rows(rows, employee):
	return {(row["leave_type"], row["level"], row["balance"]) for row in rows if row["employee"] == employee}


def set_alert_settings(**values):
	settings = frappe.get_single("Nortix Leave Settings")
	settings.update(
		{
			"is_balance_alert_enabled": 1,
			"balance_alert_role": "HR Manager",
			"low_balance_days": 2,
			"critical_balance_days": 0,
		}
	)
	settings.update(values)
	settings.save()


class TestBalanceAlerts(IntegrationTestCase):
	"""LV-010: low (2 days or less) and critical (0) balances, per company, in a report and a weekly summary."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		for company, abbr in ((COMPANY_A, "_TNA"), (COMPANY_B, "_TNB")):
			make_company(company, abbr)
			make_leave_period(company)
			make_holiday_list_for(company, abbr)
		make_leave_type()
		set_annual_settings(is_annual_allocation_enabled=0)
		set_leave_settings(
			is_casual_allocation_enabled=0,
			is_additional_allocation_enabled=0,
			is_medical_allocation_enabled=0,
		)
		set_alert_settings()

	def setUp(self):
		frappe.db.savepoint("nortix_alert_test")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback(save_point="nortix_alert_test")

	def test_low_and_critical_thresholds(self):
		employee = make_employee(COMPANY_A, "2024-01-01")
		allocate(employee, COMPANY_A, CASUAL_LEAVE_TYPE, 6)
		take_leave(employee, COMPANY_A, CASUAL_LEAVE_TYPE, "2026-03-02", "2026-03-05")
		allocate(employee, COMPANY_A, ADDITIONAL_LEAVE_TYPE, 1)
		take_leave(employee, COMPANY_A, ADDITIONAL_LEAVE_TYPE, "2026-04-01", "2026-04-01")
		allocate(employee, COMPANY_A, MEDICAL_LEAVE_TYPE, 2.5)
		allocate(employee, COMPANY_A, ANNUAL_LEAVE_TYPE, 3)
		self.assertEqual(
			alert_rows(get_balance_alerts(ON_DATE), employee),
			{(CASUAL_LEAVE_TYPE, "Low", 2), (ADDITIONAL_LEAVE_TYPE, "Critical", 0)},
		)

	def test_pending_leave_does_not_reduce_balance(self):
		employee = make_employee(COMPANY_A, "2024-01-02")
		allocate(employee, COMPANY_A, MEDICAL_LEAVE_TYPE, 3)
		take_leave(employee, COMPANY_A, MEDICAL_LEAVE_TYPE, "2026-05-04", "2026-05-04", status="Open")
		self.assertEqual(alert_rows(get_balance_alerts(ON_DATE), employee), set())

	def test_leave_type_without_allocation_is_not_flagged(self):
		employee = make_employee(COMPANY_A, "2026-06-01")
		self.assertEqual(alert_rows(get_balance_alerts(ON_DATE), employee), set())

	def test_thresholds_come_from_settings(self):
		employee = make_employee(COMPANY_A, "2024-01-03")
		allocate(employee, COMPANY_A, MEDICAL_LEAVE_TYPE, 2.5)
		set_alert_settings(low_balance_days=3)
		self.assertEqual(
			alert_rows(get_balance_alerts(ON_DATE), employee), {(MEDICAL_LEAVE_TYPE, "Low", 2.5)}
		)

	def test_left_employee_is_not_flagged(self):
		employee = make_employee(COMPANY_A, "2024-01-04")
		allocate(employee, COMPANY_A, MEDICAL_LEAVE_TYPE, 1)
		frappe.db.set_value("Employee", employee, {"status": "Left", "relieving_date": "2026-06-01"})
		self.assertEqual(alert_rows(get_balance_alerts(ON_DATE), employee), set())

	def test_report_shows_only_users_companies(self):
		from frappe.desk.query_report import run as run_report

		own = make_employee(COMPANY_A, "2024-01-05")
		other = make_employee(COMPANY_B, "2024-01-05")
		allocate(own, COMPANY_A, MEDICAL_LEAVE_TYPE, 1)
		allocate(other, COMPANY_B, MEDICAL_LEAVE_TYPE, 1)
		frappe.set_user(
			make_user("nortix.alert.hr.a@example.com", ["HR User", "Employee"], company=COMPANY_A)
		)
		result = run_report("Leave Balance Alerts", filters={"date": ON_DATE})
		reported = {row.get("employee") for row in result["result"] if isinstance(row, dict)}
		self.assertIn(own, reported)
		self.assertNotIn(other, reported)

	def test_employee_role_cannot_run_report(self):
		from frappe.desk.query_report import run as run_report

		frappe.set_user(make_user("nortix.alert.employee@example.com", ["Employee"]))
		with self.assertRaises(frappe.PermissionError):
			run_report("Leave Balance Alerts", filters={"date": ON_DATE})

	def test_weekly_summary_per_recipient_company(self):
		own = make_employee(COMPANY_A, "2024-01-06")
		other = make_employee(COMPANY_B, "2024-01-06")
		allocate(own, COMPANY_A, MEDICAL_LEAVE_TYPE, 1)
		allocate(other, COMPANY_B, MEDICAL_LEAVE_TYPE, 1)
		manager_a = make_user("nortix.alert.hrm.a@example.com", ["HR Manager", "Employee"], company=COMPANY_A)
		manager_b = make_user("nortix.alert.hrm.b@example.com", ["HR Manager", "Employee"], company=COMPANY_B)

		with patch("nortix.hr_leave.services.balance_alerts.frappe.sendmail") as sendmail:
			sent = send_weekly_alerts(ON_DATE)
		messages = {call.kwargs["recipients"][0]: call.kwargs["message"] for call in sendmail.call_args_list}
		self.assertIn(manager_a, sent)
		self.assertIn(manager_b, sent)
		self.assertIn(own, messages[manager_a])
		self.assertNotIn(other, messages[manager_a])
		self.assertIn(other, messages[manager_b])
		self.assertNotIn(own, messages[manager_b])

	def test_weekly_summary_skips_users_without_role(self):
		employee = make_employee(COMPANY_A, "2024-01-07")
		allocate(employee, COMPANY_A, MEDICAL_LEAVE_TYPE, 1)
		hr_user = make_user("nortix.alert.hruser@example.com", ["HR User", "Employee"], company=COMPANY_A)
		with patch("nortix.hr_leave.services.balance_alerts.frappe.sendmail"):
			sent = send_weekly_alerts(ON_DATE)
		self.assertNotIn(hr_user, sent)

	def test_weekly_summary_disabled_sends_nothing(self):
		employee = make_employee(COMPANY_A, "2024-01-08")
		allocate(employee, COMPANY_A, MEDICAL_LEAVE_TYPE, 1)
		set_alert_settings(is_balance_alert_enabled=0)
		with patch("nortix.hr_leave.services.balance_alerts.frappe.sendmail") as sendmail:
			self.assertEqual(send_weekly_alerts(ON_DATE), [])
		sendmail.assert_not_called()

	def test_critical_above_low_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			set_alert_settings(low_balance_days=1, critical_balance_days=2)

	def test_enabled_alerts_require_role(self):
		with self.assertRaises(frappe.ValidationError):
			set_alert_settings(balance_alert_role=None)
