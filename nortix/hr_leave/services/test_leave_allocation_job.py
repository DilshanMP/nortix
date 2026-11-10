from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from nortix.hr_leave import tasks
from nortix.hr_leave.services.allocation_source import allow_allocation_source
from nortix.hr_leave.services.leave_allocation_job import allocate_due_leave
from nortix.hr_leave.testing import (
	ADDITIONAL_LEAVE_TYPE,
	CASUAL_LEAVE_TYPE,
	COMPANY_A,
	COMPANY_B,
	MEDICAL_LEAVE_TYPE,
	make_company,
	make_employee,
	make_leave_period,
	make_leave_type,
	make_user,
	set_annual_settings,
	set_leave_settings,
)


def allocations(employee, leave_type, docstatus=1):
	return frappe.get_all(
		"Leave Allocation",
		filters={"employee": employee, "leave_type": leave_type, "docstatus": docstatus},
		fields=[
			"name",
			"from_date",
			"to_date",
			"new_leaves_allocated",
			"total_leaves_allocated",
			"company",
			"nortix_source",
		],
	)


def adjustments(allocation, docstatus=1):
	return frappe.get_all(
		"Leave Adjustment",
		filters={"leave_allocation": allocation, "docstatus": docstatus},
		fields=["name", "leaves_to_adjust", "posting_date", "adjustment_type"],
	)


def casual_total(employee):
	[allocation] = allocations(employee, CASUAL_LEAVE_TYPE)
	return allocation.new_leaves_allocated + sum(a.leaves_to_adjust for a in adjustments(allocation.name))


class TestLeaveAllocationJob(IntegrationTestCase):
	"""LV-003, LV-004, LV-005, LV-007: daily allocation of casual, additional and medical leave."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		make_company(COMPANY_A, "_TNA")
		make_company(COMPANY_B, "_TNB")
		make_leave_period(COMPANY_A)
		make_leave_period(COMPANY_B)
		make_leave_type()
		set_annual_settings(is_annual_allocation_enabled=0)
		set_leave_settings()

	def setUp(self):
		frappe.db.savepoint("nortix_leave_job_test")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback(save_point="nortix_leave_job_test")

	def test_casual_joining_year_granted_up_front(self):
		employee = make_employee(COMPANY_A, "2026-05-10")
		summary = allocate_due_leave("2026-05-10")
		[allocation] = allocations(employee, CASUAL_LEAVE_TYPE)
		self.assertEqual(
			(str(allocation.from_date), str(allocation.to_date), allocation.new_leaves_allocated),
			("2026-05-10", "2026-12-31", 4),
		)
		self.assertEqual(allocation.nortix_source, "casual_rule")
		self.assertEqual(allocation.company, COMPANY_A)
		self.assertIn(allocation.name, summary["created"])

	def test_casual_rises_to_7_on_mark_date_once(self):
		employee = make_employee(COMPANY_A, "2025-11-01")
		allocate_due_leave("2026-01-01")
		self.assertEqual(casual_total(employee), 6)
		allocate_due_leave("2026-10-31")
		self.assertEqual(casual_total(employee), 6)

		summary = allocate_due_leave("2026-11-01")
		self.assertEqual(casual_total(employee), 7)
		[allocation] = allocations(employee, CASUAL_LEAVE_TYPE)
		[adjustment] = adjustments(allocation.name)
		self.assertEqual((str(adjustment.posting_date), adjustment.leaves_to_adjust), ("2026-11-01", 1))
		self.assertIn(adjustment.name, summary["adjusted"])

		again = allocate_due_leave("2026-11-02")
		self.assertEqual(casual_total(employee), 7)
		self.assertEqual(again["adjusted"], [])
		self.assertNotIn(employee, again["failed"])

	def test_casual_first_run_after_mark_allocates_7(self):
		employee = make_employee(COMPANY_A, "2025-03-01")
		allocate_due_leave("2026-06-01")
		[allocation] = allocations(employee, CASUAL_LEAVE_TYPE)
		self.assertEqual((str(allocation.from_date), allocation.new_leaves_allocated), ("2026-01-01", 7))
		self.assertEqual(adjustments(allocation.name), [])

	def test_casual_migration_allocation_is_not_topped_up(self):
		employee = make_employee(COMPANY_A, "2025-11-02")
		doc = frappe.get_doc(
			{
				"doctype": "Leave Allocation",
				"employee": employee,
				"company": COMPANY_A,
				"leave_type": CASUAL_LEAVE_TYPE,
				"from_date": "2026-01-01",
				"to_date": "2026-12-31",
				"new_leaves_allocated": 6,
				"nortix_source": "migration",
			}
		)
		with allow_allocation_source():
			doc.insert()
			doc.submit()
		summary = allocate_due_leave("2026-11-02")
		self.assertIn(employee, summary["skipped"])
		self.assertEqual(adjustments(doc.name), [])

	def test_cancelled_top_up_is_not_recreated(self):
		employee = make_employee(COMPANY_A, "2025-11-03")
		allocate_due_leave("2026-01-01")
		allocate_due_leave("2026-11-03")
		allocation = allocations(employee, CASUAL_LEAVE_TYPE)[0].name
		frappe.get_doc("Leave Adjustment", adjustments(allocation)[0].name).cancel()
		summary = allocate_due_leave("2026-11-04")
		self.assertEqual(adjustments(allocation), [])
		self.assertEqual(summary["adjusted"], [])

	def test_additional_ends_day_before_mark(self):
		employee = make_employee(COMPANY_A, "2025-11-05")
		allocate_due_leave("2026-01-01")
		[allocation] = allocations(employee, ADDITIONAL_LEAVE_TYPE)
		self.assertEqual(
			(str(allocation.from_date), str(allocation.to_date), allocation.new_leaves_allocated),
			("2026-01-01", "2026-11-04", 1),
		)
		self.assertEqual(allocation.nortix_source, "additional_rule")

	def test_no_additional_from_mark_date(self):
		employee = make_employee(COMPANY_A, "2025-11-06")
		allocate_due_leave("2026-11-06")
		self.assertEqual(allocations(employee, ADDITIONAL_LEAVE_TYPE), [])

	def test_medical_full_amount_for_december_joiner(self):
		employee = make_employee(COMPANY_A, "2026-12-30")
		allocate_due_leave("2026-12-30")
		[allocation] = allocations(employee, MEDICAL_LEAVE_TYPE)
		self.assertEqual((str(allocation.from_date), allocation.new_leaves_allocated), ("2026-12-30", 7))
		self.assertEqual(allocation.nortix_source, "medical_rule")

	def test_duplicate_run_creates_nothing_new(self):
		employee = make_employee(COMPANY_A, "2026-02-10")
		first = allocate_due_leave("2026-02-10")
		second = allocate_due_leave("2026-02-10")
		self.assertEqual(len(first["created"]), 3)
		self.assertEqual(second["created"], [])
		self.assertIn(employee, second["skipped"])
		self.assertNotIn(employee, second["failed"])
		for leave_type in (CASUAL_LEAVE_TYPE, ADDITIONAL_LEAVE_TYPE, MEDICAL_LEAVE_TYPE):
			self.assertEqual(len(allocations(employee, leave_type)), 1)

	def test_cancelled_job_allocation_is_not_recreated(self):
		employee = make_employee(COMPANY_A, "2026-02-11")
		allocate_due_leave("2026-02-11")
		frappe.get_doc("Leave Allocation", allocations(employee, MEDICAL_LEAVE_TYPE)[0].name).cancel()
		allocate_due_leave("2026-02-12")
		self.assertEqual(allocations(employee, MEDICAL_LEAVE_TYPE), [])

	def test_disabled_type_creates_nothing_for_that_type(self):
		employee = make_employee(COMPANY_A, "2026-02-12")
		set_leave_settings(is_casual_allocation_enabled=0)
		allocate_due_leave("2026-02-12")
		self.assertEqual(allocations(employee, CASUAL_LEAVE_TYPE), [])
		self.assertEqual(len(allocations(employee, MEDICAL_LEAVE_TYPE)), 1)

	def test_daily_task_runs_enabled_types(self):
		employee = make_employee(COMPANY_A, "2026-02-13")
		with patch("nortix.hr_leave.tasks.today", return_value="2026-02-13"):
			tasks.daily()
		self.assertEqual(len(allocations(employee, MEDICAL_LEAVE_TYPE)), 1)

	def test_failed_submit_leaves_no_draft(self):
		from hrms.hr.doctype.leave_allocation.leave_allocation import LeaveAllocation

		failing = make_employee(COMPANY_A, "2026-02-14")
		working = make_employee(COMPANY_A, "2026-02-14")
		original_on_submit = LeaveAllocation.on_submit

		def fail_on_submit(allocation):
			if allocation.employee == failing:
				raise frappe.ValidationError("simulated submit failure")
			return original_on_submit(allocation)

		with patch.object(LeaveAllocation, "on_submit", fail_on_submit):
			summary = allocate_due_leave("2026-02-14")
		self.assertIn(failing, summary["failed"])
		for leave_type in (CASUAL_LEAVE_TYPE, MEDICAL_LEAVE_TYPE):
			self.assertEqual(allocations(failing, leave_type, docstatus=0), [])
			self.assertEqual(allocations(failing, leave_type), [])
			self.assertEqual(len(allocations(working, leave_type)), 1)

	def test_other_company_hr_user_cannot_read_allocation(self):
		own = make_employee(COMPANY_A, "2026-02-15")
		other = make_employee(COMPANY_B, "2026-02-15")
		allocate_due_leave("2026-02-15")
		own_allocation = allocations(own, CASUAL_LEAVE_TYPE)[0].name
		other_allocation = allocations(other, CASUAL_LEAVE_TYPE)[0].name
		frappe.set_user(
			make_user("nortix.leave.hr.a@example.com", ["HR User", "Employee"], company=COMPANY_A)
		)
		self.assertTrue(frappe.has_permission("Leave Allocation", "read", own_allocation))
		self.assertFalse(frappe.has_permission("Leave Allocation", "read", other_allocation))
		visible = frappe.get_list(
			"Leave Allocation", filters={"employee": ["in", [own, other]]}, pluck="name"
		)
		self.assertIn(own_allocation, visible)
		self.assertNotIn(other_allocation, visible)
