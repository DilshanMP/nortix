from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

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

HR_A = "nortix.med.hr.a@example.com"
HR_B = "nortix.med.hr.b@example.com"
BACKUP = "nortix.med.backup@example.com"
MANAGER = "nortix.med.manager@example.com"
OUTSIDER = "nortix.med.outsider@example.com"


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


def apply(employee, company, leave_type=MEDICAL_LEAVE_TYPE, day="2026-04-06"):
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


def backup_emails(sendmail):
	return [
		call for call in sendmail.call_args_list if "backup" in (call.kwargs.get("subject") or "").lower()
	]


class TestMedicalApproval(IntegrationTestCase):
	"""LV-007, LV-009, Q23: HR approves medical leave; named backups may approve and HR is told."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		for company, abbr in ((COMPANY_A, "_TNA"), (COMPANY_B, "_TNB")):
			make_company(company, abbr)
			make_leave_period(company)
			make_holiday_list_for(company, abbr)
		make_leave_type()
		make_user(HR_A, ["HR Manager", "Employee"], company=COMPANY_A)
		make_user(HR_B, ["HR Manager", "Employee"], company=COMPANY_B)
		make_user(BACKUP, ["Leave Approver", "Employee"])
		make_user(MANAGER, ["Leave Approver", "Employee"])
		make_user(OUTSIDER, ["Leave Approver", "Employee"])
		set_annual_settings(is_annual_allocation_enabled=0)
		set_leave_settings(
			is_casual_allocation_enabled=0,
			is_additional_allocation_enabled=0,
			is_medical_allocation_enabled=0,
			medical_leave_approver=HR_A,
			medical_backup_approvers=[{"user": BACKUP}],
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

	def test_medical_application_goes_to_named_hr_user(self):
		application = apply(self.employee, COMPANY_A)
		self.assertEqual(application.leave_approver, HR_A)
		casual = apply(self.employee, COMPANY_A, CASUAL_LEAVE_TYPE, "2026-04-07")
		self.assertEqual(casual.leave_approver, MANAGER)

	def test_hr_user_can_approve(self):
		application = apply(self.employee, COMPANY_A)
		self.assertEqual(decide(application, HR_A).docstatus, 1)

	def test_backup_can_approve_and_company_hr_is_emailed(self):
		application = apply(self.employee, COMPANY_A)
		with patch("frappe.sendmail") as sendmail:
			doc = decide(application, BACKUP)
		self.assertEqual(doc.docstatus, 1)
		[email] = backup_emails(sendmail)
		self.assertIn(HR_A, email.kwargs["recipients"])
		self.assertNotIn(HR_B, email.kwargs["recipients"])
		self.assertIn(self.employee, email.kwargs["message"])
		self.assertIn(BACKUP, email.kwargs["message"])

	def test_hr_approval_sends_no_backup_email(self):
		application = apply(self.employee, COMPANY_A)
		with patch("frappe.sendmail") as sendmail:
			decide(application, HR_A)
		self.assertEqual(backup_emails(sendmail), [])

	def test_backup_rejection_is_also_reported(self):
		application = apply(self.employee, COMPANY_A)
		with patch("frappe.sendmail") as sendmail:
			decide(application, BACKUP, status="Rejected")
		self.assertEqual(len(backup_emails(sendmail)), 1)

	def test_reporting_manager_cannot_approve_medical_but_can_approve_casual(self):
		medical = apply(self.employee, COMPANY_A)
		with self.assertRaises(frappe.PermissionError):
			decide(medical, MANAGER)
		casual = apply(self.employee, COMPANY_A, CASUAL_LEAVE_TYPE, "2026-04-07")
		self.assertEqual(decide(casual, MANAGER).docstatus, 1)

	def test_backup_cannot_decide_own_medical_leave(self):
		own = make_employee(COMPANY_A, "2024-01-02")
		frappe.db.set_value("Employee", own, "user_id", BACKUP)
		allocate(own, COMPANY_A, MEDICAL_LEAVE_TYPE)
		application = apply(own, COMPANY_A)
		with self.assertRaises(frappe.PermissionError):
			decide(application, BACKUP)

	def test_outsider_refused_through_api(self):
		from frappe.client import submit as client_submit

		application = apply(self.employee, COMPANY_A)
		frappe.share.add_docshare(
			"Leave Application",
			application.name,
			OUTSIDER,
			write=1,
			submit=1,
			flags={"ignore_share_permission": True},
		)
		doc = frappe.get_doc("Leave Application", application.name).as_dict()
		doc["status"] = "Approved"
		frappe.set_user(OUTSIDER)
		with self.assertRaises(frappe.PermissionError):
			client_submit(doc)

	def test_backup_receives_share_and_loses_it_when_removed(self):
		application = apply(self.employee, COMPANY_A)

		def shared_with(user):
			return frappe.db.exists(
				"DocShare",
				{"share_doctype": "Leave Application", "share_name": application.name, "user": user},
			)

		self.assertTrue(shared_with(BACKUP))
		set_leave_settings(medical_backup_approvers=[])
		self.assertFalse(shared_with(BACKUP))

	def test_medical_approver_must_be_hr(self):
		with self.assertRaisesRegex(frappe.ValidationError, "HR"):
			set_leave_settings(medical_leave_approver=MANAGER)

	def test_disabled_backup_rejected(self):
		disabled = make_user("nortix.med.disabled@example.com", ["Leave Approver", "Employee"])
		frappe.db.set_value("User", disabled, "enabled", 0)
		with self.assertRaisesRegex(frappe.ValidationError, "enabled"):
			set_leave_settings(medical_backup_approvers=[{"user": disabled}])

	def test_backup_without_leave_approver_role_rejected(self):
		plain = make_user("nortix.med.plain@example.com", ["Employee"])
		with self.assertRaisesRegex(frappe.ValidationError, "Leave Approver role"):
			set_leave_settings(medical_backup_approvers=[{"user": plain}])
