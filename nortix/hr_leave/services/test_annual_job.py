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

	def tearDown(self):
		frappe.set_user("Administrator")

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
		allocate_due_annual_leave("2026-03-01")
		allocate_due_annual_leave("2026-03-01")
		allocate_due_annual_leave("2026-03-02")
		self.assertEqual(len(allocations(employee)), 1)

	def test_skips_employee_with_migration_allocation(self):
		employee = make_employee(COMPANY_A, "2025-01-15")
		make_allocation(employee, COMPANY_A, "2026-01-15", 9, "migration")
		allocate_due_annual_leave("2026-02-01")
		[allocation] = allocations(employee)
		self.assertEqual((allocation.nortix_source, allocation.new_leaves_allocated), ("migration", 9))

	def test_skips_employee_with_manual_allocation(self):
		employee = make_employee(COMPANY_A, "2025-01-16")
		make_allocation(employee, COMPANY_A, "2026-01-16", 12, "manual")
		allocate_due_annual_leave("2026-02-01")
		self.assertEqual([a.nortix_source for a in allocations(employee)], ["manual"])

	def test_does_not_recreate_cancelled_job_allocation(self):
		employee = make_employee(COMPANY_A, "2025-01-17")
		allocate_due_annual_leave("2026-02-01")
		frappe.get_doc("Leave Allocation", allocations(employee)[0].name).cancel()
		allocate_due_annual_leave("2026-02-02")
		self.assertEqual(allocations(employee), [])

	def test_skips_left_employee(self):
		employee = make_employee(COMPANY_A, "2025-01-18", status="Left")
		allocate_due_annual_leave("2026-02-01")
		self.assertEqual(allocations(employee), [])

	def test_company_without_active_leave_period_is_skipped(self):
		employee = make_employee(COMPANY_NO_PERIOD, "2025-01-19")
		summary = allocate_due_annual_leave("2026-02-01")
		self.assertEqual(allocations(employee), [])
		self.assertIn(COMPANY_NO_PERIOD, summary["companies_without_period"])

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

	def test_unsuitable_leave_type_stops_run_with_one_log(self):
		employee = make_employee(COMPANY_A, "2025-01-25")
		frappe.db.set_value("Leave Type", ANNUAL_LEAVE_TYPE, "allow_over_allocation", 0)
		try:
			summary = allocate_due_annual_leave("2026-02-01")
		finally:
			frappe.db.set_value("Leave Type", ANNUAL_LEAVE_TYPE, "allow_over_allocation", 1)
		self.assertEqual(summary["not_run"], "annual leave type not suitable")
		self.assertEqual(summary["failed"], [])
		self.assertEqual(allocations(employee), [])
		self.assertTrue(latest_error_log("Annual leave allocation not run"))

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
