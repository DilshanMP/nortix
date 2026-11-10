"""Read queries for the HR Leave module."""

import frappe


def get_active_leave_periods(on_date) -> list[frappe._dict]:
	"""Active Leave Periods that cover `on_date`, one or more per company (LV-002, LV-006)."""
	period = frappe.qb.DocType("Leave Period")
	return (
		frappe.qb.from_(period)
		.select(period.name, period.company, period.from_date, period.to_date)
		.where((period.is_active == 1) & (period.from_date <= on_date) & (period.to_date >= on_date))
		.orderby(period.company)
		.orderby(period.from_date)
	).run(as_dict=True)


def get_active_employees_joined_by(company: str, on_date) -> list[frappe._dict]:
	"""Active employees of `company` who joined on or before `on_date` (LV-006)."""
	employee = frappe.qb.DocType("Employee")
	return (
		frappe.qb.from_(employee)
		.select(employee.name, employee.company, employee.date_of_joining)
		.where(
			(employee.company == company)
			& (employee.status == "Active")
			& (employee.date_of_joining <= on_date)
		)
		.orderby(employee.name)
	).run(as_dict=True)


def get_companies_with_active_employees() -> list[str]:
	employee = frappe.qb.DocType("Employee")
	return (
		frappe.qb.from_(employee).select(employee.company).distinct().where(employee.status == "Active")
	).run(pluck=True)


def get_employees_with_annual_allocation(
	employees: list[str], leave_type: str, from_date, to_date, job_source: str
) -> set[str]:
	"""Employees already handled for this leave type and period (LV-006, Q16).

	A draft or submitted allocation from any source counts, so migrated and manual allocations
	are never doubled. A cancelled allocation counts only if the job created it: HR cancels to
	correct, and the job must not undo that correction.
	"""
	if not employees:
		return set()
	allocation = frappe.qb.DocType("Leave Allocation")
	rows = (
		frappe.qb.from_(allocation)
		.select(allocation.employee)
		.distinct()
		.where(
			allocation.employee.isin(employees)
			& (allocation.leave_type == leave_type)
			& (allocation.from_date <= to_date)
			& (allocation.to_date >= from_date)
			& (
				allocation.docstatus.isin([0, 1])
				| ((allocation.docstatus == 2) & (allocation.nortix_source == job_source))
			)
		)
	).run(pluck=True)
	return set(rows)
