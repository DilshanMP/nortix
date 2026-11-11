from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on

from nortix.hr_leave import tasks
from nortix.hr_leave.services.allocation_source import allow_allocation_source
from nortix.hr_leave.services.leave_allocation_job import RUN_LOCK, allocate_due_leave
from nortix.hr_leave.testing import (
	ADDITIONAL_LEAVE_TYPE,
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

RULE_TYPES = (CASUAL_LEAVE_TYPE, ADDITIONAL_LEAVE_TYPE, MEDICAL_LEAVE_TYPE)


def allocations(employee, leave_type, docstatus=1):
	return frappe.get_all(
		"Leave Allocation",
		filters={"employee": employee, "leave_type": leave_type, "docstatus": docstatus},
		fields=["name", "from_date", "to_date", "new_leaves_allocated", "company", "nortix_source"],
	)


def adjustments(allocation, docstatus=(0, 1, 2)):
	return frappe.get_all(
		"Leave Adjustment",
		filters={"leave_allocation": allocation, "docstatus": ["in", list(docstatus)]},
		fields=["name", "leaves_to_adjust", "posting_date", "company", "nortix_source", "docstatus"],
	)


def casual_balance(employee, on_date):
	return get_leave_balance_on(
		employee, CASUAL_LEAVE_TYPE, on_date, consider_all_leaves_in_the_allocation_period=True
	)


def make_allocation(employee, company, leave_type, from_date, days, source=None):
	doc = frappe.get_doc(
		{
			"doctype": "Leave Allocation",
			"employee": employee,
			"company": company,
			"leave_type": leave_type,
			"from_date": from_date,
			"to_date": "2026-12-31",
			"new_leaves_allocated": days,
			"nortix_source": source,
		}
	)
	with allow_allocation_source():
		doc.insert()
		doc.submit()
	return doc


def hr_adjustment(allocation, adjustment_type="Reduce", submit=True):
	doc = frappe.get_doc(
		{
			"doctype": "Leave Adjustment",
			"employee": frappe.db.get_value("Leave Allocation", allocation, "employee"),
			"leave_type": CASUAL_LEAVE_TYPE,
			"leave_allocation": allocation,
			"adjustment_type": adjustment_type,
			"leaves_to_adjust": 0.5,
			"posting_date": "2026-03-01",
		}
	).insert()
	if submit:
		doc.submit()
	return doc


class TestLeaveAllocationJob(IntegrationTestCase):
	"""LV-003, LV-004, LV-005, LV-007: daily allocation of casual, additional and medical leave."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		for company, abbr in ((COMPANY_A, "_TNA"), (COMPANY_B, "_TNB")):
			make_company(company, abbr)
			make_leave_period(company)
			make_holiday_list_for(company, abbr)
		make_company(COMPANY_NO_PERIOD, "_TNC")
		make_leave_type()
		set_annual_settings(is_annual_allocation_enabled=0)
		set_leave_settings()

	def setUp(self):
		frappe.db.savepoint("nortix_leave_job_test")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback(save_point="nortix_leave_job_test")

	# LV-003 casual leave before the mark

	def test_casual_joining_year_granted_up_front(self):
		employee = make_employee(COMPANY_A, "2026-05-10")
		summary = allocate_due_leave("2026-05-10")
		[allocation] = allocations(employee, CASUAL_LEAVE_TYPE)
		self.assertEqual(
			(str(allocation.from_date), str(allocation.to_date), allocation.new_leaves_allocated),
			("2026-05-10", "2026-12-31", 4),
		)
		self.assertEqual((allocation.nortix_source, allocation.company), ("casual_rule", COMPANY_A))
		self.assertIn(allocation.name, summary["created"])

	def test_changed_amounts_do_not_top_up_existing_allocations(self):
		joiner = make_employee(COMPANY_A, "2026-05-11")
		before_mark = make_employee(COMPANY_A, "2025-11-11")
		allocate_due_leave("2026-05-11")
		set_leave_settings(casual_monthly_days_first_year=1, casual_days_before_mark=6.5)
		summary = allocate_due_leave("2026-06-01")
		self.assertEqual(summary["adjusted"], [])
		for employee in (joiner, before_mark):
			[allocation] = allocations(employee, CASUAL_LEAVE_TYPE)
			self.assertEqual(adjustments(allocation.name), [])
		self.assertEqual(allocations(joiner, CASUAL_LEAVE_TYPE)[0].new_leaves_allocated, 4)

	# LV-004 casual leave from the mark

	def test_casual_rises_to_7_on_mark_date_once(self):
		employee = make_employee(COMPANY_A, "2025-11-01")
		allocate_due_leave("2026-01-01")
		self.assertEqual(casual_balance(employee, "2026-10-31"), 6)
		allocate_due_leave("2026-10-31")
		self.assertEqual(casual_balance(employee, "2026-10-31"), 6)

		summary = allocate_due_leave("2026-11-01")
		self.assertEqual(casual_balance(employee, "2026-11-01"), 7)
		[allocation] = allocations(employee, CASUAL_LEAVE_TYPE)
		[adjustment] = adjustments(allocation.name)
		self.assertEqual(
			(str(adjustment.posting_date), adjustment.leaves_to_adjust, adjustment.nortix_source),
			("2026-11-01", 1, "casual_rule"),
		)
		self.assertIn(adjustment.name, summary["adjusted"])

		again = allocate_due_leave("2026-11-02")
		self.assertEqual(again["adjusted"], [])
		self.assertIn(employee, again["skipped"])
		self.assertNotIn(employee, again["failed"])
		self.assertEqual(casual_balance(employee, "2026-11-02"), 7)

	def test_five_taken_before_mark_leaves_two_after_mark(self):
		employee = make_employee(COMPANY_A, "2025-11-03")
		allocate_due_leave("2026-01-01")
		take_leave(employee, COMPANY_A, CASUAL_LEAVE_TYPE, "2026-03-02", "2026-03-06")
		allocate_due_leave("2026-11-03")
		self.assertEqual(casual_balance(employee, "2026-11-03"), 2)

	def test_top_up_after_missed_mark_posts_on_mark_date(self):
		employee = make_employee(COMPANY_A, "2025-08-15")
		allocate_due_leave("2026-01-01")
		allocate_due_leave("2026-09-30")
		[allocation] = allocations(employee, CASUAL_LEAVE_TYPE)
		[adjustment] = adjustments(allocation.name)
		self.assertEqual(str(adjustment.posting_date), "2026-08-15")

	def test_casual_first_run_after_mark_allocates_7_without_top_up(self):
		employee = make_employee(COMPANY_A, "2025-03-01")
		allocate_due_leave("2026-06-01")
		[allocation] = allocations(employee, CASUAL_LEAVE_TYPE)
		self.assertEqual((str(allocation.from_date), allocation.new_leaves_allocated), ("2026-01-01", 7))
		self.assertEqual(adjustments(allocation.name), [])

	def test_migrated_casual_allocation_rises_at_mark(self):
		employee = make_employee(COMPANY_A, "2025-11-04")
		migrated = make_allocation(employee, COMPANY_A, CASUAL_LEAVE_TYPE, "2026-01-01", 6, "migration")
		summary = allocate_due_leave("2026-11-04")
		self.assertEqual(len(allocations(employee, CASUAL_LEAVE_TYPE)), 1)
		[adjustment] = adjustments(migrated.name)
		self.assertIn(adjustment.name, summary["adjusted"])
		self.assertEqual(casual_balance(employee, "2026-11-04"), 7)

	def test_hr_adjustment_before_mark_is_reported_not_overridden(self):
		employee = make_employee(COMPANY_A, "2025-11-05")
		allocate_due_leave("2026-01-01")
		allocation = allocations(employee, CASUAL_LEAVE_TYPE)[0].name
		hr_adjustment(allocation)
		summary = allocate_due_leave("2026-11-05")
		self.assertIn(employee, summary["needs_review"])
		[log] = frappe.get_all(
			"Error Log",
			filters={"method": "Leave allocation needs review"},
			fields=["error"],
			order_by="creation desc",
			limit=1,
		)
		self.assertIn(employee, log.error)
		self.assertNotIn(employee, summary["failed"])
		self.assertEqual(len(adjustments(allocation)), 1)

	def test_hr_draft_adjustment_does_not_block_top_up(self):
		employee = make_employee(COMPANY_A, "2025-11-06")
		allocate_due_leave("2026-01-01")
		allocation = allocations(employee, CASUAL_LEAVE_TYPE)[0].name
		hr_adjustment(allocation, adjustment_type="Allocate", submit=False)
		summary = allocate_due_leave("2026-11-06")
		self.assertEqual(len(summary["adjusted"]), 1)
		self.assertEqual(casual_balance(employee, "2026-11-06"), 7)

	def test_cancelled_top_up_is_not_recreated(self):
		employee = make_employee(COMPANY_A, "2025-11-07")
		allocate_due_leave("2026-01-01")
		allocate_due_leave("2026-11-07")
		allocation = allocations(employee, CASUAL_LEAVE_TYPE)[0].name
		frappe.get_doc("Leave Adjustment", adjustments(allocation)[0].name).cancel()
		summary = allocate_due_leave("2026-11-08")
		self.assertEqual(summary["adjusted"], [])
		self.assertIn(employee, summary["skipped"])
		self.assertEqual(adjustments(allocation, docstatus=(0, 1)), [])

	def test_failed_top_up_leaves_no_adjustment_and_retries(self):
		from hrms.hr.doctype.leave_adjustment.leave_adjustment import LeaveAdjustment

		employee = make_employee(COMPANY_A, "2025-11-09")
		allocate_due_leave("2026-01-01")
		allocation = allocations(employee, CASUAL_LEAVE_TYPE)[0].name

		def fail_on_submit(adjustment):
			raise frappe.ValidationError("simulated submit failure")

		with patch.object(LeaveAdjustment, "on_submit", fail_on_submit):
			summary = allocate_due_leave("2026-11-09")
		self.assertIn(employee, summary["failed"])
		self.assertEqual(adjustments(allocation), [])

		retry = allocate_due_leave("2026-11-10")
		self.assertEqual(len(retry["adjusted"]), 1)
		self.assertEqual(casual_balance(employee, "2026-11-10"), 7)

	def test_hr_user_cannot_set_adjustment_source(self):
		from frappe.client import insert as client_insert

		employee = make_employee(COMPANY_A, "2025-11-12")
		allocate_due_leave("2026-01-01")
		allocation = allocations(employee, CASUAL_LEAVE_TYPE)[0].name
		frappe.set_user(
			make_user("nortix.leave.hr.a@example.com", ["HR User", "Employee"], company=COMPANY_A)
		)
		with self.assertRaises(frappe.PermissionError):
			client_insert(
				{
					"doctype": "Leave Adjustment",
					"employee": employee,
					"leave_type": CASUAL_LEAVE_TYPE,
					"leave_allocation": allocation,
					"adjustment_type": "Allocate",
					"leaves_to_adjust": 1,
					"posting_date": "2026-03-01",
					"nortix_source": "casual_rule",
				}
			)

	# LV-005 additional leave

	def test_additional_ends_day_before_mark(self):
		employee = make_employee(COMPANY_A, "2025-11-13")
		allocate_due_leave("2026-01-01")
		[allocation] = allocations(employee, ADDITIONAL_LEAVE_TYPE)
		self.assertEqual(
			(str(allocation.from_date), str(allocation.to_date), allocation.new_leaves_allocated),
			("2026-01-01", "2026-11-12", 1),
		)
		self.assertEqual(allocation.nortix_source, "additional_rule")

	def test_no_additional_from_mark_date(self):
		employee = make_employee(COMPANY_A, "2025-11-14")
		allocate_due_leave("2026-11-14")
		self.assertEqual(allocations(employee, ADDITIONAL_LEAVE_TYPE), [])
		self.assertEqual(len(allocations(employee, CASUAL_LEAVE_TYPE)), 1)

	def test_additional_cannot_be_taken_from_mark_date(self):
		employee = make_employee(COMPANY_A, "2025-11-16")
		allocate_due_leave("2026-01-01")
		take_leave(employee, COMPANY_A, CASUAL_LEAVE_TYPE, "2026-11-16", "2026-11-16")
		with self.assertRaisesRegex(frappe.ValidationError, "(?i)balance|allocat"):
			take_leave(employee, COMPANY_A, ADDITIONAL_LEAVE_TYPE, "2026-11-17", "2026-11-17")

	def test_additional_taken_before_mark_shows_taken_not_overdraft(self):
		from hrms.hr.doctype.leave_application.leave_application import get_leaves_for_period

		employee = make_employee(COMPANY_A, "2025-11-17")
		allocate_due_leave("2026-01-01")
		take_leave(employee, COMPANY_A, ADDITIONAL_LEAVE_TYPE, "2026-06-01", "2026-06-01")
		self.assertEqual(get_leave_balance_on(employee, ADDITIONAL_LEAVE_TYPE, "2026-11-20"), 0)
		self.assertEqual(
			get_leaves_for_period(employee, ADDITIONAL_LEAVE_TYPE, "2026-01-01", "2026-12-31"), -1
		)

	# LV-007 medical leave

	def test_medical_full_amount_for_december_joiner(self):
		employee = make_employee(COMPANY_A, "2026-12-30")
		allocate_due_leave("2026-12-30")
		[allocation] = allocations(employee, MEDICAL_LEAVE_TYPE)
		self.assertEqual((str(allocation.from_date), allocation.new_leaves_allocated), ("2026-12-30", 7))
		self.assertEqual(allocation.nortix_source, "medical_rule")

	# Job behaviour shared by all rules

	def test_duplicate_run_creates_nothing_new(self):
		employee = make_employee(COMPANY_A, "2026-02-10")
		first = allocate_due_leave("2026-02-10")
		second = allocate_due_leave("2026-02-10")
		self.assertEqual(len(first["created"]), 3)
		self.assertEqual(second["created"], [])
		self.assertIn(employee, second["skipped"])
		self.assertNotIn(employee, second["failed"])
		for leave_type in RULE_TYPES:
			self.assertEqual(len(allocations(employee, leave_type)), 1)

	def test_cancelled_job_allocation_is_not_recreated(self):
		employee = make_employee(COMPANY_A, "2026-02-11")
		allocate_due_leave("2026-02-11")
		frappe.get_doc("Leave Allocation", allocations(employee, MEDICAL_LEAVE_TYPE)[0].name).cancel()
		summary = allocate_due_leave("2026-02-12")
		self.assertEqual(allocations(employee, MEDICAL_LEAVE_TYPE), [])
		self.assertIn(employee, summary["skipped"])

	def test_disabled_type_creates_nothing_for_that_type(self):
		employee = make_employee(COMPANY_A, "2026-02-12")
		set_leave_settings(is_casual_allocation_enabled=0)
		allocate_due_leave("2026-02-12")
		self.assertEqual(allocations(employee, CASUAL_LEAVE_TYPE), [])
		self.assertEqual(len(allocations(employee, MEDICAL_LEAVE_TYPE)), 1)

	def test_daily_task_runs_leave_rules_without_annual_switch(self):
		employee = make_employee(COMPANY_A, "2026-02-13")
		with patch("nortix.hr_leave.tasks.today", return_value="2026-02-13"):
			tasks.daily()
		for leave_type in RULE_TYPES:
			self.assertEqual(len(allocations(employee, leave_type)), 1)

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
		for leave_type in RULE_TYPES:
			self.assertEqual(allocations(failing, leave_type, docstatus=0), [])
			self.assertEqual(allocations(failing, leave_type), [])
			self.assertEqual(len(allocations(working, leave_type)), 1)

	def test_join_after_run_date_gives_nothing(self):
		employee = make_employee(COMPANY_A, "2026-03-01")
		allocate_due_leave("2026-02-15")
		for leave_type in RULE_TYPES:
			self.assertEqual(allocations(employee, leave_type), [])

	def test_left_employee_gets_nothing(self):
		employee = make_employee(COMPANY_A, "2025-06-01", status="Left", relieving_date="2026-01-31")
		allocate_due_leave("2026-02-15")
		for leave_type in RULE_TYPES:
			self.assertEqual(allocations(employee, leave_type), [])

	def test_company_without_period_is_reported(self):
		employee = make_employee(COMPANY_NO_PERIOD, "2025-06-02")
		summary = allocate_due_leave("2026-02-15")
		self.assertIn(COMPANY_NO_PERIOD, summary["companies_without_period"])
		self.assertEqual(allocations(employee, MEDICAL_LEAVE_TYPE), [])

	def test_period_not_calendar_year_is_reported(self):
		period = make_leave_period(COMPANY_NO_PERIOD, "2025-04-01", "2026-03-31")
		employee = make_employee(COMPANY_NO_PERIOD, "2025-06-03")
		summary = allocate_due_leave("2026-02-15")
		self.assertIn(period, summary["periods_not_calendar_year"])
		self.assertEqual(allocations(employee, MEDICAL_LEAVE_TYPE), [])

	def test_second_run_stops_while_first_holds_lock(self):
		from frappe.utils.synchronization import filelock

		employee = make_employee(COMPANY_A, "2026-02-16")
		with filelock(RUN_LOCK, timeout=1):
			summary = allocate_due_leave("2026-02-16")
		self.assertIn("already running", summary["not_run"])
		self.assertEqual(allocations(employee, MEDICAL_LEAVE_TYPE), [])

	def test_unsuitable_leave_type_stops_only_that_rule(self):
		employee = make_employee(COMPANY_A, "2026-02-17")
		logs_before = frappe.db.count("Error Log", {"method": "Leave allocation not run"})
		frappe.db.set_value("Leave Type", MEDICAL_LEAVE_TYPE, "allow_over_allocation", 0)
		try:
			summary = allocate_due_leave("2026-02-17")
		finally:
			frappe.db.set_value("Leave Type", MEDICAL_LEAVE_TYPE, "allow_over_allocation", 1)
		self.assertIn("medical leave type not suitable", summary["not_run"])
		self.assertEqual(allocations(employee, MEDICAL_LEAVE_TYPE), [])
		self.assertEqual(len(allocations(employee, CASUAL_LEAVE_TYPE)), 1)
		self.assertEqual(
			frappe.db.count("Error Log", {"method": "Leave allocation not run"}), logs_before + 1
		)

	def test_other_company_hr_user_cannot_read_allocation_or_adjustment(self):
		own = make_employee(COMPANY_A, "2025-11-18")
		other = make_employee(COMPANY_B, "2025-11-18")
		allocate_due_leave("2026-01-01")
		allocate_due_leave("2026-11-18")
		own_allocation = allocations(own, CASUAL_LEAVE_TYPE)[0]
		other_allocation = allocations(other, CASUAL_LEAVE_TYPE)[0]
		self.assertEqual(other_allocation.company, COMPANY_B)
		[other_adjustment] = adjustments(other_allocation.name)
		[own_adjustment] = adjustments(own_allocation.name)
		self.assertEqual(other_adjustment.company, COMPANY_B)

		frappe.set_user(
			make_user("nortix.leave.hr.a@example.com", ["HR User", "Employee"], company=COMPANY_A)
		)
		self.assertTrue(frappe.has_permission("Leave Allocation", "read", own_allocation.name))
		self.assertFalse(frappe.has_permission("Leave Allocation", "read", other_allocation.name))
		self.assertTrue(frappe.has_permission("Leave Adjustment", "read", own_adjustment.name))
		self.assertFalse(frappe.has_permission("Leave Adjustment", "read", other_adjustment.name))
		visible = frappe.get_list(
			"Leave Allocation", filters={"employee": ["in", [own, other]]}, pluck="name"
		)
		self.assertIn(own_allocation.name, visible)
		self.assertNotIn(other_allocation.name, visible)
		visible_adjustments = frappe.get_list(
			"Leave Adjustment", filters={"employee": ["in", [own, other]]}, pluck="name"
		)
		self.assertIn(own_adjustment.name, visible_adjustments)
		self.assertNotIn(other_adjustment.name, visible_adjustments)
