import frappe
from frappe.tests import IntegrationTestCase

from nortix.hr_leave.services.annual import validate_annual_leave_type
from nortix.hr_leave.testing import (
	ANNUAL_LEAVE_TYPE,
	COMPANY_A,
	make_company,
	make_leave_type,
	make_user,
	set_annual_settings,
)

# The tests create their own Leave Types; the generated ones pull in records from apps
# that are not installed (Leave Type -> Salary Component -> Payment Gateway).
IGNORE_TEST_RECORD_DEPENDENCIES = ["Leave Type"]


class TestNortixLeaveSettings(IntegrationTestCase):
	"""LV-006, LV-011: annual leave values are validated settings, changed only by HR managers."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		make_leave_type()
		make_leave_type("_Test Nortix No Over Allocation", allow_over_allocation=0)
		make_leave_type("_Test Nortix Carry Forward", is_carry_forward=1)

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_valid_settings_save(self):
		set_annual_settings()
		self.assertEqual(frappe.db.get_single_value("Nortix Leave Settings", "annual_q2_days"), 10)

	def test_negative_amount_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			set_annual_settings(annual_q3_days=-1)

	def test_amount_over_a_year_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			set_annual_settings(annual_full_days=367)

	def test_enabled_requires_annual_leave_type(self):
		with self.assertRaises(frappe.ValidationError):
			set_annual_settings(annual_leave_type=None)

	def test_disabled_allows_missing_leave_type(self):
		set_annual_settings(is_annual_allocation_enabled=0, annual_leave_type=None)

	def test_leave_type_must_allow_over_allocation(self):
		with self.assertRaises(frappe.ValidationError):
			set_annual_settings(annual_leave_type="_Test Nortix No Over Allocation")

	def test_carry_forward_leave_type_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			set_annual_settings(annual_leave_type="_Test Nortix Carry Forward")

	def test_leave_type_maximum_below_largest_amount_rejected(self):
		make_leave_type(ANNUAL_LEAVE_TYPE, max_leaves_allowed=10)
		try:
			with self.assertRaises(frappe.ValidationError):
				set_annual_settings()
		finally:
			make_leave_type(ANNUAL_LEAVE_TYPE, max_leaves_allowed=0)

	def test_employee_role_cannot_change_settings(self):
		set_annual_settings()
		frappe.set_user(make_user("nortix.settings.employee@example.com", ["Employee"]))
		with self.assertRaises(frappe.PermissionError):
			set_annual_settings(annual_q1_days=20)

	def test_hr_user_can_read_not_write(self):
		frappe.set_user(make_user("nortix.settings.hruser@example.com", ["HR User", "Employee"]))
		self.assertTrue(frappe.has_permission("Nortix Leave Settings", "read"))
		self.assertFalse(frappe.has_permission("Nortix Leave Settings", "write"))

	def test_company_hr_manager_cannot_change_settings(self):
		# The settings apply to every company on the site, so an HR Manager limited to one
		# company must not be able to change them.
		make_company(COMPANY_A, "_TNA")
		set_annual_settings()
		frappe.set_user(
			make_user("nortix.settings.hrmanager@example.com", ["HR Manager", "Employee"], company=COMPANY_A)
		)
		self.assertTrue(frappe.has_permission("Nortix Leave Settings", "read"))
		with self.assertRaises(frappe.PermissionError):
			set_annual_settings(annual_q4_days=5)

	def test_system_manager_can_change_settings(self):
		frappe.set_user(make_user("nortix.settings.sysmanager@example.com", ["System Manager"]))
		set_annual_settings(annual_q4_days=5)
		self.assertEqual(frappe.db.get_single_value("Nortix Leave Settings", "annual_q4_days"), 5)

	def test_settings_change_is_recorded_in_version(self):
		set_annual_settings(annual_q2_days=10)
		settings = frappe.get_single("Nortix Leave Settings")
		settings.annual_q2_days = 11
		# Frappe skips versions during tests unless asked; production saves always record them.
		settings.save(ignore_version=False)
		versions = frappe.get_all(
			"Version",
			filters={"ref_doctype": "Nortix Leave Settings", "docname": "Nortix Leave Settings"},
			fields=["data"],
			order_by="creation desc",
			limit=1,
		)
		self.assertTrue(versions)
		self.assertIn("annual_q2_days", versions[0].data)

	def test_missing_leave_type_rejected_with_clear_message(self):
		settings = frappe._dict(annual_leave_type="_Test Nortix Missing Type", annual_full_days=14)
		with self.assertRaisesRegex(frappe.ValidationError, "does not exist"):
			validate_annual_leave_type(settings)
