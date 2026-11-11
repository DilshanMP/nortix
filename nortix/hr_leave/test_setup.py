import frappe
from frappe.tests import IntegrationTestCase

from nortix.hr_leave.setup import check_app_permission, setup_leave_types
from nortix.hr_leave.testing import make_user


class TestLeaveSetup(IntegrationTestCase):
	"""LV-001: the four leave types from the leave Sheet, and who sees the Nortix tile."""

	def setUp(self):
		frappe.db.savepoint("nortix_setup_test")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback(save_point="nortix_setup_test")

	def test_leave_types_created_and_linked_once(self):
		setup_leave_types()
		self.assertEqual(setup_leave_types(), [])
		expected = {"Casual Leave": 0, "Additional Leave": 0, "Annual Leave": 1, "Medical Leave": 1}
		for name, over_allocation in expected.items():
			leave_type = frappe.db.get_value(
				"Leave Type",
				name,
				["allow_over_allocation", "is_carry_forward", "is_earned_leave"],
				as_dict=True,
			)
			self.assertEqual(
				(leave_type.allow_over_allocation, leave_type.is_carry_forward, leave_type.is_earned_leave),
				(over_allocation, 0, 0),
			)
		settings = frappe.get_single("Nortix Leave Settings")
		self.assertEqual(settings.medical_leave_type, "Medical Leave")
		self.assertFalse(settings.is_annual_allocation_enabled)

	def test_tile_shown_to_hr_not_to_employees(self):
		frappe.set_user(make_user("nortix.tile.hr@example.com", ["HR User", "Employee"]))
		self.assertTrue(check_app_permission())
		frappe.set_user("Administrator")
		frappe.set_user(make_user("nortix.tile.employee@example.com", ["Employee"]))
		self.assertFalse(check_app_permission())
