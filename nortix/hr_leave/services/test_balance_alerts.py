from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from nortix.hr_leave import tasks
from nortix.hr_leave.services import balance_alerts
from nortix.hr_leave.services.balance_alerts import classify_balance, get_balance_alerts, send_weekly_alerts
from nortix.hr_leave.testing import (
	ADDITIONAL_LEAVE_TYPE,
	ANNUAL_LEAVE_TYPE,
	CASUAL_LEAVE_TYPE,
	COMPANY_A,
	COMPANY_B,
	COMPANY_NO_PERIOD,
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
		allocate(employee, COMPANY_A, CASUAL_LEAVE_TYPE, 1)
		self.assertEqual(alert_rows(get_balance_alerts(ON_DATE), employee), {(CASUAL_LEAVE_TYPE, "Low", 1)})

	def test_thresholds_come_from_settings(self):
		employee = make_employee(COMPANY_A, "2024-01-03")
		allocate(employee, COMPANY_A, MEDICAL_LEAVE_TYPE, 2.5)
		set_alert_settings(low_balance_days=3)
		self.assertEqual(
			alert_rows(get_balance_alerts(ON_DATE), employee), {(MEDICAL_LEAVE_TYPE, "Low", 2.5)}
		)

	def test_only_active_employees_are_flagged(self):
		active = make_employee(COMPANY_A, "2024-01-04")
		allocate(active, COMPANY_A, MEDICAL_LEAVE_TYPE, 1)
		others = []
		for status in ("Left", "Inactive", "Suspended"):
			employee = make_employee(COMPANY_A, "2024-01-04")
			allocate(employee, COMPANY_A, MEDICAL_LEAVE_TYPE, 1)
			frappe.db.set_value("Employee", employee, {"status": status, "relieving_date": "2026-06-01"})
			others.append(employee)
		rows = get_balance_alerts(ON_DATE)
		self.assertEqual(alert_rows(rows, active), {(MEDICAL_LEAVE_TYPE, "Low", 1)})
		for employee in others:
			self.assertEqual(alert_rows(rows, employee), set())

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
		manager = make_user("nortix.alert.hrm.a@example.com", ["HR Manager", "Employee"], company=COMPANY_A)
		with patch("nortix.hr_leave.services.balance_alerts.frappe.sendmail") as sendmail:
			sent = send_weekly_alerts(ON_DATE)
		recipients = {call.kwargs["recipients"][0] for call in sendmail.call_args_list}
		self.assertIn(manager, recipients)
		self.assertNotIn(hr_user, recipients)
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

	def test_report_company_filter_cannot_reach_other_company(self):
		from frappe.desk.query_report import run as run_report

		own = make_employee(COMPANY_A, "2024-01-09")
		other = make_employee(COMPANY_B, "2024-01-09")
		allocate(own, COMPANY_A, MEDICAL_LEAVE_TYPE, 1)
		allocate(other, COMPANY_B, MEDICAL_LEAVE_TYPE, 1)
		frappe.set_user(
			make_user("nortix.alert.hr.a@example.com", ["HR User", "Employee"], company=COMPANY_A)
		)

		def reported(company):
			result = run_report("Leave Balance Alerts", filters={"date": ON_DATE, "company": company})
			return {row.get("employee") for row in result["result"] if isinstance(row, dict)}

		self.assertIn(own, reported(COMPANY_A))
		self.assertNotIn(other, reported(COMPANY_B))

	def test_report_export_shows_only_users_companies(self):
		import json

		from frappe.desk.query_report import export_query

		own = make_employee(COMPANY_A, "2024-01-10")
		other = make_employee(COMPANY_B, "2024-01-10")
		allocate(own, COMPANY_A, MEDICAL_LEAVE_TYPE, 1)
		allocate(other, COMPANY_B, MEDICAL_LEAVE_TYPE, 1)
		frappe.set_user(
			make_user("nortix.alert.hrm.a@example.com", ["HR Manager", "Employee"], company=COMPANY_A)
		)
		saved = frappe.local.form_dict
		try:
			frappe.local.form_dict = frappe._dict(
				report_name="Leave Balance Alerts",
				file_format_type="CSV",
				filters=json.dumps({"date": ON_DATE}),
			)
			export_query()
			exported = frappe.safe_decode(frappe.response["filecontent"])
		finally:
			frappe.local.form_dict = saved
		self.assertIn(own, exported)
		self.assertNotIn(other, exported)

	def test_unrestricted_manager_skipped_by_default(self):
		employee = make_employee(COMPANY_A, "2024-01-11")
		allocate(employee, COMPANY_A, MEDICAL_LEAVE_TYPE, 1)
		restricted = make_user(
			"nortix.alert.hrm.a@example.com", ["HR Manager", "Employee"], company=COMPANY_A
		)
		unrestricted = make_user("nortix.alert.hrm.all@example.com", ["HR Manager", "Employee"])
		with patch("nortix.hr_leave.services.balance_alerts.frappe.sendmail") as sendmail:
			sent = send_weekly_alerts(ON_DATE)
		recipients = {call.kwargs["recipients"][0] for call in sendmail.call_args_list}
		self.assertIn(restricted, recipients)
		self.assertNotIn(unrestricted, recipients)
		self.assertNotIn(unrestricted, sent)

	def test_unrestricted_manager_gets_all_companies_when_allowed(self):
		own = make_employee(COMPANY_A, "2024-01-20")
		other = make_employee(COMPANY_B, "2024-01-20")
		allocate(own, COMPANY_A, MEDICAL_LEAVE_TYPE, 1)
		allocate(other, COMPANY_B, MEDICAL_LEAVE_TYPE, 1)
		manager = make_user("nortix.alert.hrm.all@example.com", ["HR Manager", "Employee"])
		set_alert_settings(is_balance_alert_to_unrestricted=1)
		with patch("nortix.hr_leave.services.balance_alerts.frappe.sendmail") as sendmail:
			send_weekly_alerts(ON_DATE)
		messages = {call.kwargs["recipients"][0]: call.kwargs["message"] for call in sendmail.call_args_list}
		self.assertIn(own, messages[manager])
		self.assertIn(other, messages[manager])

	def test_employee_role_rejected_as_recipient(self):
		for role in ("Employee", "Employee Self Service"):
			with self.subTest(role=role), self.assertRaisesRegex(frappe.ValidationError, "cannot receive"):
				set_alert_settings(balance_alert_role=role)

	def test_hr_user_role_accepted_as_recipient(self):
		set_alert_settings(balance_alert_role="HR User")
		self.assertEqual(frappe.db.get_single_value("Nortix Leave Settings", "balance_alert_role"), "HR User")

	def test_allocation_dates_are_inclusive(self):
		ends_before = make_employee(COMPANY_A, "2024-01-12")
		starts_on = make_employee(COMPANY_A, "2024-01-12")
		ends_on = make_employee(COMPANY_A, "2024-01-12")
		for employee, from_date, to_date in (
			(ends_before, "2026-01-01", "2026-03-31"),
			(starts_on, "2026-04-01", "2026-12-31"),
			(ends_on, "2026-01-01", "2026-04-01"),
		):
			doc = frappe.get_doc(
				{
					"doctype": "Leave Allocation",
					"employee": employee,
					"company": COMPANY_A,
					"leave_type": MEDICAL_LEAVE_TYPE,
					"from_date": from_date,
					"to_date": to_date,
					"new_leaves_allocated": 1,
				}
			).insert()
			doc.submit()
		rows = get_balance_alerts("2026-04-01")
		self.assertEqual(alert_rows(rows, ends_before), set())
		self.assertEqual(alert_rows(rows, starts_on), {(MEDICAL_LEAVE_TYPE, "Low", 1)})
		self.assertEqual(alert_rows(rows, ends_on), {(MEDICAL_LEAVE_TYPE, "Low", 1)})

	def test_cancelled_allocation_is_not_checked(self):
		employee = make_employee(COMPANY_A, "2024-01-13")
		allocate(employee, COMPANY_A, MEDICAL_LEAVE_TYPE, 1)
		allocation = frappe.get_all("Leave Allocation", {"employee": employee, "docstatus": 1}, pluck="name")[
			0
		]
		frappe.get_doc("Leave Allocation", allocation).cancel()
		self.assertEqual(alert_rows(get_balance_alerts(ON_DATE), employee), set())

	def test_cancelled_leave_restores_balance(self):
		employee = make_employee(COMPANY_A, "2024-01-14")
		allocate(employee, COMPANY_A, MEDICAL_LEAVE_TYPE, 3)
		application = take_leave(employee, COMPANY_A, MEDICAL_LEAVE_TYPE, "2026-05-05", "2026-05-05")
		self.assertEqual(alert_rows(get_balance_alerts(ON_DATE), employee), {(MEDICAL_LEAVE_TYPE, "Low", 2)})
		application.cancel()
		self.assertEqual(alert_rows(get_balance_alerts(ON_DATE), employee), set())

	def test_half_day_reaching_low(self):
		employee = make_employee(COMPANY_A, "2024-01-15")
		allocate(employee, COMPANY_A, MEDICAL_LEAVE_TYPE, 2.5)
		doc = frappe.get_doc(
			{
				"doctype": "Leave Application",
				"employee": employee,
				"company": COMPANY_A,
				"leave_type": MEDICAL_LEAVE_TYPE,
				"from_date": "2026-05-06",
				"to_date": "2026-05-06",
				"half_day": 1,
				"half_day_date": "2026-05-06",
				"posting_date": "2026-05-06",
				"status": "Approved",
			}
		).insert()
		doc.submit()
		self.assertEqual(alert_rows(get_balance_alerts(ON_DATE), employee), {(MEDICAL_LEAVE_TYPE, "Low", 2)})

	def test_weekly_task_sends_summary_for_today(self):
		self.assertIn("nortix.hr_leave.tasks.weekly", frappe.get_hooks("scheduler_events")["weekly"])
		with (
			patch("nortix.hr_leave.tasks.send_weekly_alerts") as send,
			patch("nortix.hr_leave.tasks.today", return_value=ON_DATE),
		):
			tasks.weekly()
		send.assert_called_once_with(ON_DATE)

	def test_disabled_user_gets_no_summary(self):
		employee = make_employee(COMPANY_A, "2024-01-16")
		allocate(employee, COMPANY_A, MEDICAL_LEAVE_TYPE, 1)
		enabled = make_user("nortix.alert.hrm.a@example.com", ["HR Manager", "Employee"], company=COMPANY_A)
		disabled = make_user(
			"nortix.alert.hrm.off@example.com", ["HR Manager", "Employee"], company=COMPANY_A
		)
		frappe.db.set_value("User", disabled, "enabled", 0)
		with patch("nortix.hr_leave.services.balance_alerts.frappe.sendmail"):
			sent = send_weekly_alerts(ON_DATE)
		self.assertIn(enabled, sent)
		self.assertNotIn(disabled, sent)

	def test_recipient_with_nothing_to_report_gets_no_email(self):
		make_company(COMPANY_NO_PERIOD, "_TNC")
		employee = make_employee(COMPANY_A, "2024-01-17")
		allocate(employee, COMPANY_A, MEDICAL_LEAVE_TYPE, 1)
		busy = make_user("nortix.alert.hrm.a@example.com", ["HR Manager", "Employee"], company=COMPANY_A)
		idle = make_user(
			"nortix.alert.hrm.c@example.com", ["HR Manager", "Employee"], company=COMPANY_NO_PERIOD
		)
		with patch("nortix.hr_leave.services.balance_alerts.frappe.sendmail") as sendmail:
			sent = send_weekly_alerts(ON_DATE)
		recipients = {call.kwargs["recipients"][0] for call in sendmail.call_args_list}
		self.assertIn(busy, recipients)
		self.assertNotIn(idle, recipients)
		self.assertNotIn(idle, sent)

	def test_failure_for_one_recipient_does_not_stop_others(self):
		employee = make_employee(COMPANY_A, "2024-01-18")
		allocate(employee, COMPANY_A, MEDICAL_LEAVE_TYPE, 1)
		first = make_user("nortix.alert.hrm.a@example.com", ["HR Manager", "Employee"], company=COMPANY_A)
		second = make_user("nortix.alert.hrm.z@example.com", ["HR Manager", "Employee"], company=COMPANY_A)
		original = balance_alerts._employees_visible_to
		logs_before = frappe.db.count("Error Log", {"method": "Leave balance summary not sent"})

		def fail_first(user):
			if user == first:
				raise frappe.PermissionError
			return original(user)

		with (
			patch.object(balance_alerts, "_employees_visible_to", side_effect=fail_first),
			patch("nortix.hr_leave.services.balance_alerts.frappe.sendmail"),
		):
			sent = send_weekly_alerts(ON_DATE)
		self.assertNotIn(first, sent)
		self.assertIn(second, sent)
		self.assertEqual(
			frappe.db.count("Error Log", {"method": "Leave balance summary not sent"}), logs_before + 1
		)

	def test_negative_critical_rejected(self):
		with self.assertRaisesRegex(frappe.ValidationError, "at least 0"):
			set_alert_settings(critical_balance_days=-1)

	def test_low_above_a_year_rejected(self):
		with self.assertRaisesRegex(frappe.ValidationError, "at most 366"):
			set_alert_settings(low_balance_days=367)

	def test_equal_thresholds_allowed_and_classify_as_critical(self):
		set_alert_settings(low_balance_days=1, critical_balance_days=1)
		employee = make_employee(COMPANY_A, "2024-01-19")
		allocate(employee, COMPANY_A, MEDICAL_LEAVE_TYPE, 1)
		self.assertEqual(
			alert_rows(get_balance_alerts(ON_DATE), employee), {(MEDICAL_LEAVE_TYPE, "Critical", 1)}
		)


class TestBalanceClassification(UnitTestCase):
	"""LV-010: thresholds are inclusive; anything at or below critical is Critical."""

	def test_boundaries(self):
		settings = frappe._dict(low_balance_days=2, critical_balance_days=0)
		cases = {-1: "Critical", 0: "Critical", 0.5: "Low", 2: "Low", 2.01: None, 2.5: None}
		for balance, level in cases.items():
			with self.subTest(balance=balance):
				self.assertEqual(classify_balance(balance, settings), level)


class TestSummaryRendering(UnitTestCase):
	"""LV-010: names and companies are user-entered, so the email escapes them."""

	def test_summary_escapes_html(self):
		html = balance_alerts._render_summary(
			[
				{
					"employee": "HR-EMP-1",
					"employee_name": "<script>x</script> & Co",
					"company": "A & B",
					"leave_type": "Casual",
					"balance": 1,
					"level": "Low",
				}
			],
			ON_DATE,
		)
		self.assertIn("&lt;script&gt;", html)
		self.assertIn("&amp; Co", html)
		self.assertNotIn("<script>", html)
