from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from nortix.hr_leave import tasks
from nortix.hr_leave.services import annual
from nortix.hr_leave.services.allocation_source import allow_allocation_source
from nortix.hr_leave.services.annual import ALLOCATION_SOURCE, RUN_LOCK, allocate_due_annual_leave
from nortix.hr_leave.testing import (
	ANNUAL_LEAVE_TYPE,
	COMPANY_A,
	COMPANY_B,
	COMPANY_NO_PERIOD,
	make_company,
	make_employee,
	make_leave_period,
	make_leave_type,
	make_user,
	set_annual_settings,
)


def allocations(employee, docstatus=1):
	return frappe.get_all(
		"Leave Allocation",
		filters={"employee": employee, "leave_type": ANNUAL_LEAVE_TYPE, "docstatus": docstatus},
		fields=["name", "from_date", "to_date", "new_leaves_allocated", "company", "nortix_source"],
	)


def make_allocation(employee, company, from_date, days, source):
	doc = frappe.get_doc(
		{
			"doctype": "Leave Allocation",
			"employee": employee,
			"company": company,
			"leave_type": ANNUAL_LEAVE_TYPE,
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


def latest_error_log(title):
	return frappe.get_all(
		"Error Log",
		filters={"method": title},
		fields=["error", "reference_name"],
		order_by="creation desc",
		limit=1,
	)


class TestAnnualAllocationJob(IntegrationTestCase):
	"""LV-006: the daily job creates one annual allocation per employee and period, per company."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		make_company(COMPANY_A, "_TNA")
		make_company(COMPANY_B, "_TNB")
		make_company(COMPANY_NO_PERIOD, "_TNC")
		make_leave_type()
		cls.period_a = make_leave_period(COMPANY_A)
		cls.period_b = make_leave_period(COMPANY_B)
		set_annual_settings()

	def setUp(self):
		# Each job run touches every Active employee on the site, so every test starts from the
		# same data and leaves nothing behind for the next one.
		frappe.db.savepoint("nortix_job_test")
		self.form_dict = frappe.local.form_dict

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.local.form_dict = self.form_dict
		frappe.db.rollback(save_point="nortix_job_test")

	def test_creates_submitted_allocation_with_source_and_company(self):
		employee = make_employee(COMPANY_A, "2025-05-20")
		summary = allocate_due_annual_leave("2026-06-01")
		[allocation] = allocations(employee)
		self.assertEqual(allocation.company, COMPANY_A)
		self.assertEqual(allocation.nortix_source, ALLOCATION_SOURCE)
		self.assertEqual(str(allocation.from_date), "2026-05-20")
		self.assertEqual(str(allocation.to_date), "2026-12-31")
		self.assertEqual(allocation.new_leaves_allocated, 10)
		self.assertIn(allocation.name, summary["created"])

	def test_mark_1_nov_gives_4_days_from_mark_date(self):
		employee = make_employee(COMPANY_A, "2025-11-01")
		allocate_due_annual_leave("2026-10-31")
		self.assertEqual(allocations(employee), [])
		allocate_due_annual_leave("2026-11-01")
		[allocation] = allocations(employee)
		self.assertEqual((str(allocation.from_date), allocation.new_leaves_allocated), ("2026-11-01", 4))

	def test_mark_31_mar_and_1_apr(self):
		march = make_employee(COMPANY_A, "2025-03-31")
		april = make_employee(COMPANY_A, "2025-04-01")
		allocate_due_annual_leave("2026-04-01")
		self.assertEqual(allocations(march)[0].new_leaves_allocated, 14)
		self.assertEqual(allocations(april)[0].new_leaves_allocated, 10)

	def test_mark_31_dec_allocates_4_days(self):
		employee = make_employee(COMPANY_A, "2025-12-31")
		allocate_due_annual_leave("2026-12-31")
		[allocation] = allocations(employee)
		self.assertEqual((str(allocation.from_date), allocation.new_leaves_allocated), ("2026-12-31", 4))

	def test_later_period_gets_full_days(self):
		employee = make_employee(COMPANY_A, "2024-08-10")
		allocate_due_annual_leave("2026-01-01")
		[allocation] = allocations(employee)
		self.assertEqual((str(allocation.from_date), allocation.new_leaves_allocated), ("2026-01-01", 14))

	def test_duplicate_run_creates_one_allocation(self):
		employee = make_employee(COMPANY_A, "2025-02-10")
		first = allocate_due_annual_leave("2026-03-01")
		second = allocate_due_annual_leave("2026-03-01")
		third = allocate_due_annual_leave("2026-03-02")
		self.assertEqual(len(allocations(employee)), 1)
		self.assertEqual(len(first["created"]), 1)
		for summary in (second, third):
			self.assertIn(employee, summary["skipped"])
			self.assertNotIn(employee, summary["failed"])
			self.assertEqual(summary["created"], [])

	def test_skips_employee_with_migration_allocation(self):
		employee = make_employee(COMPANY_A, "2025-01-15")
		make_allocation(employee, COMPANY_A, "2026-01-15", 9, "migration")
		summary = allocate_due_annual_leave("2026-02-01")
		self.assertIn(employee, summary["skipped"])
		self.assertNotIn(employee, summary["failed"])
		[allocation] = allocations(employee)
		self.assertEqual((allocation.nortix_source, allocation.new_leaves_allocated), ("migration", 9))

	def test_skips_employee_with_manual_allocation(self):
		employee = make_employee(COMPANY_A, "2025-01-16")
		make_allocation(employee, COMPANY_A, "2026-01-16", 12, "manual")
		summary = allocate_due_annual_leave("2026-02-01")
		self.assertIn(employee, summary["skipped"])
		self.assertNotIn(employee, summary["failed"])
		self.assertEqual([a.nortix_source for a in allocations(employee)], ["manual"])

	def test_cancelled_migration_allocation_does_not_block_job(self):
		employee = make_employee(COMPANY_A, "2025-01-28")
		make_allocation(employee, COMPANY_A, "2026-01-28", 9, "migration").cancel()
		summary = allocate_due_annual_leave("2026-02-01")
		[allocation] = allocations(employee)
		self.assertEqual((allocation.nortix_source, allocation.new_leaves_allocated), (ALLOCATION_SOURCE, 14))
		self.assertIn(allocation.name, summary["created"])

	def test_draft_manual_allocation_blocks_job(self):
		employee = make_employee(COMPANY_A, "2025-01-29")
		frappe.get_doc(
			{
				"doctype": "Leave Allocation",
				"employee": employee,
				"company": COMPANY_A,
				"leave_type": ANNUAL_LEAVE_TYPE,
				"from_date": "2026-01-29",
				"to_date": "2026-12-31",
				"new_leaves_allocated": 3,
			}
		).insert()
		summary = allocate_due_annual_leave("2026-02-01")
		self.assertIn(employee, summary["skipped"])
		self.assertEqual(allocations(employee), [])

	def test_does_not_recreate_cancelled_job_allocation(self):
		employee = make_employee(COMPANY_A, "2025-01-17")
		allocate_due_annual_leave("2026-02-01")
		frappe.get_doc("Leave Allocation", allocations(employee)[0].name).cancel()
		allocate_due_annual_leave("2026-02-02")
		self.assertEqual(allocations(employee), [])

	def test_skips_left_employee(self):
		employee = make_employee(COMPANY_A, "2025-01-18", status="Left", relieving_date="2026-01-31")
		allocate_due_annual_leave("2026-02-01")
		self.assertEqual(allocations(employee), [])

	def test_company_without_active_leave_period_is_skipped(self):
		employee = make_employee(COMPANY_NO_PERIOD, "2025-01-19")
		summary = allocate_due_annual_leave("2026-02-01")
		self.assertEqual(allocations(employee), [])
		self.assertIn(COMPANY_NO_PERIOD, summary["companies_without_period"])

	def test_join_after_run_date_gives_nothing(self):
		employee = make_employee(COMPANY_A, "2026-03-01")
		allocate_due_annual_leave("2026-02-01")
		self.assertEqual(allocations(employee), [])

	def test_inactive_leave_period_is_ignored(self):
		make_leave_period(COMPANY_NO_PERIOD, is_active=0)
		employee = make_employee(COMPANY_NO_PERIOD, "2025-01-30")
		summary = allocate_due_annual_leave("2026-02-01")
		self.assertEqual(allocations(employee), [])
		self.assertIn(COMPANY_NO_PERIOD, summary["companies_without_period"])

	def test_period_not_calendar_year_is_reported_not_allocated(self):
		period = make_leave_period(COMPANY_NO_PERIOD, "2025-04-01", "2026-03-31")
		employee = make_employee(COMPANY_NO_PERIOD, "2025-01-31")
		summary = allocate_due_annual_leave("2026-02-01")
		self.assertEqual(allocations(employee), [])
		self.assertIn(period, summary["periods_not_calendar_year"])

	def test_changed_amount_applies_to_new_allocations_only(self):
		before = make_employee(COMPANY_A, "2025-10-05")
		allocate_due_annual_leave("2026-10-05")
		set_annual_settings(annual_q4_days=5)
		after = make_employee(COMPANY_A, "2025-10-06")
		allocate_due_annual_leave("2026-10-06")
		self.assertEqual(allocations(before)[0].new_leaves_allocated, 4)
		self.assertEqual(allocations(after)[0].new_leaves_allocated, 5)

	def test_disabled_switch_creates_nothing(self):
		employee = make_employee(COMPANY_A, "2025-01-20")
		set_annual_settings(is_annual_allocation_enabled=0)
		try:
			with patch("nortix.hr_leave.tasks.today", return_value="2026-02-01"):
				tasks.daily()
			self.assertEqual(allocations(employee), [])
		finally:
			set_annual_settings()

	def test_enabled_switch_runs_for_today(self):
		employee = make_employee(COMPANY_A, "2025-01-21")
		with patch("nortix.hr_leave.tasks.today", return_value="2026-02-01"):
			tasks.daily()
		self.assertEqual(len(allocations(employee)), 1)

	def test_one_failure_does_not_stop_others(self):
		failing = make_employee(COMPANY_A, "2025-01-22")
		working = make_employee(COMPANY_A, "2025-01-23")
		original = annual._create_allocation

		failing_name = frappe.db.get_value("Employee", failing, "employee_name")

		def fail_for_one(employee, *args, **kwargs):
			if employee.name == failing:
				raise frappe.ValidationError(f"Allocation rejected for {failing_name}")
			return original(employee, *args, **kwargs)

		with patch.object(annual, "_create_allocation", side_effect=fail_for_one):
			summary = allocate_due_annual_leave("2026-02-01")
		self.assertIn(failing, summary["failed"])
		self.assertEqual(allocations(failing), [])
		self.assertEqual(allocations(failing, docstatus=0), [])
		self.assertEqual(len(allocations(working)), 1)

		[log] = latest_error_log("Annual leave allocation failed")
		self.assertEqual(log.reference_name, failing)
		self.assertIn(failing, log.error)
		self.assertNotIn(failing_name, log.error)

	def test_failed_submit_leaves_no_draft_and_retries_next_run(self):
		from hrms.hr.doctype.leave_allocation.leave_allocation import LeaveAllocation

		failing = make_employee(COMPANY_A, "2025-02-11")
		original_on_submit = LeaveAllocation.on_submit

		def fail_on_submit(allocation):
			if allocation.employee == failing:
				raise frappe.ValidationError("simulated submit failure")
			return original_on_submit(allocation)

		with patch.object(LeaveAllocation, "on_submit", fail_on_submit):
			summary = allocate_due_annual_leave("2026-03-01")
		self.assertIn(failing, summary["failed"])
		self.assertEqual(allocations(failing, docstatus=0), [])
		self.assertEqual(allocations(failing), [])

		retry = allocate_due_annual_leave("2026-03-02")
		self.assertNotIn(failing, retry["failed"])
		self.assertEqual(len(allocations(failing)), 1)

	def test_unsuitable_leave_type_stops_run_with_one_log(self):
		employee = make_employee(COMPANY_A, "2025-01-25")
		logs_before = frappe.db.count("Error Log", {"method": "Annual leave allocation not run"})
		frappe.db.set_value("Leave Type", ANNUAL_LEAVE_TYPE, "allow_over_allocation", 0)
		try:
			summary = allocate_due_annual_leave("2026-02-01")
		finally:
			frappe.db.set_value("Leave Type", ANNUAL_LEAVE_TYPE, "allow_over_allocation", 1)
		self.assertEqual(summary["not_run"], "annual leave type not suitable")
		self.assertEqual(summary["failed"], [])
		self.assertEqual(allocations(employee), [])
		logs_after = frappe.db.count("Error Log", {"method": "Annual leave allocation not run"})
		self.assertEqual(logs_after, logs_before + 1)

	def test_second_run_stops_while_first_holds_lock(self):
		from frappe.utils.synchronization import filelock

		employee = make_employee(COMPANY_A, "2025-01-26")
		with filelock(RUN_LOCK, timeout=1):
			summary = allocate_due_annual_leave("2026-02-01")
		self.assertEqual(summary["not_run"], "already running")
		self.assertEqual(allocations(employee), [])

	def test_hr_user_cannot_set_allocation_source(self):
		from frappe.client import insert as client_insert

		employee = make_employee(COMPANY_A, "2025-01-27")
		frappe.set_user(
			make_user("nortix.leave.hr.a@example.com", ["HR User", "Employee"], company=COMPANY_A)
		)
		allocation = {
			"doctype": "Leave Allocation",
			"employee": employee,
			"company": COMPANY_A,
			"leave_type": ANNUAL_LEAVE_TYPE,
			"from_date": "2026-01-27",
			"to_date": "2026-12-31",
			"new_leaves_allocated": 5,
		}
		with self.assertRaises(frappe.PermissionError):
			client_insert({**allocation, "nortix_source": ALLOCATION_SOURCE})
		created = client_insert(allocation)
		self.assertFalse(created.get("nortix_source"))

	def test_hr_user_cannot_change_source_on_existing_allocation(self):
		from frappe.client import insert as client_insert
		from frappe.client import save as client_save

		employee = make_employee(COMPANY_A, "2025-02-12")
		frappe.set_user(
			make_user("nortix.leave.hr.a@example.com", ["HR User", "Employee"], company=COMPANY_A)
		)
		draft = client_insert(
			{
				"doctype": "Leave Allocation",
				"employee": employee,
				"company": COMPANY_A,
				"leave_type": ANNUAL_LEAVE_TYPE,
				"from_date": "2026-02-12",
				"to_date": "2026-12-31",
				"new_leaves_allocated": 5,
			}
		)
		draft["nortix_source"] = ALLOCATION_SOURCE
		with self.assertRaises(frappe.PermissionError):
			client_save(draft)

	def test_other_company_hr_user_cannot_read_allocation(self):
		own = make_employee(COMPANY_A, "2025-01-24")
		other = make_employee(COMPANY_B, "2025-01-24")
		allocate_due_annual_leave("2026-02-01")
		own_allocation = allocations(own)[0].name
		other_allocation = allocations(other)[0].name
		user = make_user("nortix.leave.hr.a@example.com", ["HR User", "Employee"], company=COMPANY_A)

		frappe.set_user(user)
		self.assertTrue(frappe.has_permission("Leave Allocation", "read", own_allocation))
		self.assertFalse(frappe.has_permission("Leave Allocation", "read", other_allocation))

		visible = frappe.get_list(
			"Leave Allocation", filters={"employee": ["in", [own, other]]}, pluck="name"
		)
		self.assertEqual(visible, [own_allocation])

		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc("Leave Allocation", other_allocation).check_permission("read")

		from frappe.client import get as client_get

		with self.assertRaises(frappe.PermissionError):
			client_get("Leave Allocation", other_allocation)

		from frappe.desk.query_report import run as run_report

		def reported_employees(company):
			result = run_report(
				"Employee Leave Balance",
				filters={"from_date": "2026-01-01", "to_date": "2026-12-31", "company": company},
			)
			return {row.get("employee") for row in result["result"] if isinstance(row, dict)}

		self.assertIn(own, reported_employees(COMPANY_A))
		self.assertNotIn(other, reported_employees(COMPANY_B))

		import json

		from frappe.desk.reportview import export_query

		# HR User has no export right on Leave Allocation; HR Manager does, so export
		# isolation is proven with an HR Manager limited to Company A.
		with self.assertRaises(frappe.PermissionError):
			frappe.local.form_dict = frappe._dict(
				doctype="Leave Allocation",
				file_format_type="CSV",
				fields=json.dumps(["`tabLeave Allocation`.`name`"]),
			)
			export_query()

		frappe.set_user("Administrator")
		hr_manager = make_user(
			"nortix.leave.hrm.a@example.com", ["HR Manager", "Employee"], company=COMPANY_A
		)
		frappe.set_user(hr_manager)
		frappe.local.form_dict = frappe._dict(
			doctype="Leave Allocation",
			file_format_type="CSV",
			fields=json.dumps(["`tabLeave Allocation`.`name`", "`tabLeave Allocation`.`employee`"]),
			filters=json.dumps({"employee": ["in", [own, other]]}),
		)
		export_query()
		exported = frappe.safe_decode(frappe.response["filecontent"])
		self.assertIn(own_allocation, exported)
		self.assertNotIn(other_allocation, exported)
