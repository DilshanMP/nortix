from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import formatdate
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on

from nortix.hr_leave.testing import (
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
)

HR_GROUP = "nortix.med.hr.group@example.com"
HR_A = "nortix.med.hr.a@example.com"
HR_USER_A = "nortix.med.hruser.a@example.com"
HR_B = "nortix.med.hr.b@example.com"
BACKUP = "nortix.med.backup@example.com"
BACKUP_B = "nortix.med.backup.b@example.com"
MANAGER = "nortix.med.manager@example.com"
OUTSIDER = "nortix.med.outsider@example.com"
DAY = "2026-04-06"

NOT_ALLOWED = "HR or a named backup"
OWN_LEAVE = "your own medical leave"


def allocate(employee, company, leave_type, days=7):
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


def apply(employee, company, leave_type=MEDICAL_LEAVE_TYPE, day=DAY):
	# The form fills in the employee's usual approver; the server keeps whatever it is given.
	return frappe.get_doc(
		{
			"doctype": "Leave Application",
			"employee": employee,
			"company": company,
			"leave_type": leave_type,
			"from_date": day,
			"to_date": day,
			"posting_date": day,
			"status": "Open",
			"leave_approver": frappe.db.get_value("Employee", employee, "leave_approver"),
		}
	).insert()


def decide(application, user, status="Approved"):
	frappe.set_user(user)
	try:
		doc = frappe.get_doc("Leave Application", application.name)
		doc.status = status
		doc.submit()
		return doc
	finally:
		frappe.set_user("Administrator")


def cancel_as(application, user):
	frappe.set_user(user)
	try:
		frappe.get_doc("Leave Application", application.name).cancel()
	finally:
		frappe.set_user("Administrator")


def emails_about(sendmail, application):
	return [call for call in sendmail.call_args_list if call.kwargs.get("reference_name") == application.name]


def share_of(application, user):
	return frappe.db.get_value(
		"DocShare",
		{"share_doctype": "Leave Application", "share_name": application.name, "user": user},
		["read", "write", "submit"],
		as_dict=True,
	)


class TestMedicalApproval(IntegrationTestCase):
	"""LV-007, LV-009, Q23, Q30, Q32: HR approves medical leave; named backups may approve within
	the companies they can see, and HR is told; only HR cancels."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		for company, abbr in ((COMPANY_A, "_TNA"), (COMPANY_B, "_TNB")):
			make_company(company, abbr)
			make_leave_period(company)
			make_holiday_list_for(company, abbr)
		make_leave_type()
		make_user(HR_GROUP, ["HR Manager", "Employee"])
		make_user(HR_A, ["HR Manager", "Employee"], company=COMPANY_A)
		make_user(HR_USER_A, ["HR User", "Employee"], company=COMPANY_A)
		make_user(HR_B, ["HR Manager", "Employee"], company=COMPANY_B)
		make_user(BACKUP, ["Leave Approver", "Employee"])
		make_user(BACKUP_B, ["Leave Approver", "Employee"], company=COMPANY_B)
		make_user(MANAGER, ["Leave Approver", "Employee"])
		make_user(OUTSIDER, ["Leave Approver", "Employee"])
		set_annual_settings(is_annual_allocation_enabled=0)
		set_leave_settings(
			is_casual_allocation_enabled=0,
			is_additional_allocation_enabled=0,
			is_medical_allocation_enabled=0,
			medical_leave_approver=HR_GROUP,
			medical_backup_approvers=[{"user": BACKUP}, {"user": BACKUP_B}],
		)

	def setUp(self):
		frappe.db.savepoint("nortix_medical_test")
		self.employee = make_employee(COMPANY_A, "2024-01-01")
		frappe.db.set_value("Employee", self.employee, "leave_approver", MANAGER)
		allocate(self.employee, COMPANY_A, MEDICAL_LEAVE_TYPE)
		allocate(self.employee, COMPANY_A, CASUAL_LEAVE_TYPE)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback(save_point="nortix_medical_test")

	# Routing

	def test_medical_application_goes_to_named_hr_user(self):
		self.assertEqual(apply(self.employee, COMPANY_A).leave_approver, HR_GROUP)
		casual = apply(self.employee, COMPANY_A, CASUAL_LEAVE_TYPE, "2026-04-07")
		self.assertEqual(casual.leave_approver, MANAGER)

	def test_changing_type_away_from_medical_restores_usual_approver(self):
		application = apply(self.employee, COMPANY_A)
		application.leave_type = CASUAL_LEAVE_TYPE
		application.save()
		self.assertEqual(application.leave_approver, MANAGER)

	# Who may decide

	def test_hr_manager_and_hr_user_can_approve(self):
		self.assertEqual(decide(apply(self.employee, COMPANY_A), HR_A).docstatus, 1)
		second = apply(self.employee, COMPANY_A, day="2026-04-08")
		self.assertEqual(decide(second, HR_USER_A).docstatus, 1)

	def test_hr_rejection_leaves_balance_unchanged(self):
		application = apply(self.employee, COMPANY_A)
		decide(application, HR_A, status="Rejected")
		self.assertEqual(get_leave_balance_on(self.employee, MEDICAL_LEAVE_TYPE, "2026-04-30"), 7)

	def test_hr_of_other_company_cannot_decide(self):
		with self.assertRaises(frappe.PermissionError):
			decide(apply(self.employee, COMPANY_A), HR_B)

	def test_reporting_manager_cannot_decide_medical_but_can_decide_casual(self):
		for status in ("Approved", "Rejected"):
			application = apply(self.employee, COMPANY_A, day="2026-04-09")
			with self.subTest(status=status), self.assertRaisesRegex(frappe.PermissionError, NOT_ALLOWED):
				decide(application, MANAGER, status=status)
			application.delete()
		casual = apply(self.employee, COMPANY_A, CASUAL_LEAVE_TYPE, "2026-04-07")
		self.assertEqual(decide(casual, MANAGER).docstatus, 1)

	def test_outsider_refused_through_api(self):
		from frappe.client import submit as client_submit

		for status in ("Approved", "Rejected"):
			application = apply(self.employee, COMPANY_A, day="2026-04-10")
			frappe.share.add_docshare(
				"Leave Application",
				application.name,
				OUTSIDER,
				submit=1,
				flags={"ignore_share_permission": True},
			)
			doc = frappe.get_doc("Leave Application", application.name).as_dict()
			doc["status"] = status
			frappe.set_user(OUTSIDER)
			with self.subTest(status=status), self.assertRaisesRegex(frappe.PermissionError, NOT_ALLOWED):
				client_submit(doc)
			frappe.set_user("Administrator")
			application.delete()

	def test_nobody_decides_own_medical_leave(self):
		for user in (BACKUP, HR_A):
			own = make_employee(COMPANY_A, "2024-01-02")
			frappe.db.set_value("Employee", own, "user_id", user)
			allocate(own, COMPANY_A, MEDICAL_LEAVE_TYPE)
			for status in ("Approved", "Rejected"):
				application = apply(own, COMPANY_A, day="2026-04-13")
				with (
					self.subTest(user=user, status=status),
					self.assertRaisesRegex(frappe.PermissionError, OWN_LEAVE),
				):
					decide(application, user, status=status)
				application.delete()

	def test_backup_sees_only_companies_their_permissions_allow(self):
		application = apply(self.employee, COMPANY_A)
		self.assertTrue(frappe.has_permission("Leave Application", "read", application.name, user=BACKUP))
		self.assertFalse(frappe.has_permission("Leave Application", "read", application.name, user=BACKUP_B))
		self.assertFalse(share_of(application, BACKUP))
		with self.assertRaises(frappe.PermissionError):
			decide(application, BACKUP_B)

	def test_backup_who_lost_the_role_cannot_decide(self):
		application = apply(self.employee, COMPANY_A)
		frappe.get_doc("User", BACKUP).remove_roles("Leave Approver")
		with self.assertRaises(frappe.PermissionError):
			decide(application, BACKUP)

	# Backup decisions and HR notice

	def test_backup_can_approve_and_hr_who_can_see_employee_is_emailed(self):
		application = apply(self.employee, COMPANY_A)
		with patch("frappe.sendmail") as sendmail:
			self.assertEqual(decide(application, BACKUP).docstatus, 1)
		[email] = emails_about(sendmail, application)
		self.assertIn(HR_A, email.kwargs["recipients"])
		self.assertIn(HR_GROUP, email.kwargs["recipients"])
		self.assertNotIn(HR_B, email.kwargs["recipients"])
		for text in (self.employee, BACKUP, formatdate(DAY)):
			self.assertIn(text, email.kwargs["message"])

	def test_backup_rejection_is_also_reported(self):
		application = apply(self.employee, COMPANY_A)
		with patch("frappe.sendmail") as sendmail:
			decide(application, BACKUP, status="Rejected")
		self.assertEqual(len(emails_about(sendmail, application)), 1)

	def test_hr_decision_sends_no_backup_notice(self):
		application = apply(self.employee, COMPANY_A)
		with patch("frappe.sendmail") as sendmail:
			decide(application, HR_A)
		notices = [
			call
			for call in emails_about(sendmail, application)
			if "backup" in (call.kwargs.get("subject") or "").lower()
		]
		self.assertEqual(notices, [])

	# Cancelling (Q32)

	def test_only_hr_can_cancel_medical_leave(self):
		application = apply(self.employee, COMPANY_A)
		decide(application, HR_A)
		for user in (MANAGER, BACKUP):
			with self.subTest(user=user), self.assertRaisesRegex(frappe.PermissionError, "Only HR"):
				cancel_as(application, user)
		cancel_as(application, HR_A)
		self.assertEqual(frappe.db.get_value("Leave Application", application.name, "docstatus"), 2)

	# Settings

	def test_medical_approver_must_be_group_wide_hr(self):
		with self.assertRaisesRegex(frappe.ValidationError, "HR"):
			set_leave_settings(medical_leave_approver=MANAGER)
		with self.assertRaisesRegex(frappe.ValidationError, "group-wide"):
			set_leave_settings(medical_leave_approver=HR_A)

	def test_disabled_backup_rejected(self):
		disabled = make_user("nortix.med.disabled@example.com", ["Leave Approver", "Employee"])
		frappe.db.set_value("User", disabled, "enabled", 0)
		with self.assertRaisesRegex(frappe.ValidationError, "enabled"):
			set_leave_settings(medical_backup_approvers=[{"user": disabled}])

	def test_backup_without_leave_approver_role_rejected(self):
		plain = make_user("nortix.med.plain@example.com", ["Employee"])
		with self.assertRaisesRegex(frappe.ValidationError, "Leave Approver role"):
			set_leave_settings(medical_backup_approvers=[{"user": plain}])
