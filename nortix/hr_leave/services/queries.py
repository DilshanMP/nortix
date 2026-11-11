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


def get_allocation_covering(employee: str, leave_type: str, on_date) -> frappe._dict | None:
	"""The submitted allocation of this leave type that covers `on_date`, whatever created it."""
	allocation = frappe.qb.DocType("Leave Allocation")
	rows = (
		frappe.qb.from_(allocation)
		.select(allocation.name, allocation.from_date, allocation.to_date, allocation.total_leaves_allocated)
		.where(
			(allocation.employee == employee)
			& (allocation.leave_type == leave_type)
			& (allocation.docstatus == 1)
			& (allocation.from_date <= on_date)
			& (allocation.to_date >= on_date)
		)
		.limit(1)
	).run(as_dict=True)
	return rows[0] if rows else None


def has_adjustment(leave_allocation: str, docstatus: tuple[int, ...], source: str | None = None) -> bool:
	"""Whether a Leave Adjustment in one of the given states (and, if given, from `source`)
	exists for the allocation."""
	adjustment = frappe.qb.DocType("Leave Adjustment")
	condition = (adjustment.leave_allocation == leave_allocation) & adjustment.docstatus.isin(list(docstatus))
	if source:
		condition &= adjustment.nortix_source == source
	return bool((frappe.qb.from_(adjustment).select(adjustment.name).where(condition).limit(1)).run())


def get_allocated_leave_types(employees: list[str], leave_types: list[str], on_date) -> set[tuple[str, str]]:
	"""(employee, leave type) pairs with a submitted allocation covering `on_date` (LV-010)."""
	if not employees or not leave_types:
		return set()
	allocation = frappe.qb.DocType("Leave Allocation")
	rows = (
		frappe.qb.from_(allocation)
		.select(allocation.employee, allocation.leave_type)
		.distinct()
		.where(
			allocation.employee.isin(employees)
			& allocation.leave_type.isin(leave_types)
			& (allocation.docstatus == 1)
			& (allocation.from_date <= on_date)
			& (allocation.to_date >= on_date)
		)
	).run()
	return {(employee, leave_type) for employee, leave_type in rows}


def get_enabled_users_with_role(role: str) -> list[str]:
	"""Enabled system users holding `role`, excluding the built-in Administrator and Guest."""
	user = frappe.qb.DocType("User")
	has_role = frappe.qb.DocType("Has Role")
	return (
		frappe.qb.from_(user)
		.join(has_role)
		.on(has_role.parent == user.name)
		.select(user.name)
		.distinct()
		.where(
			(has_role.parenttype == "User")
			& (has_role.role == role)
			& (user.enabled == 1)
			& (user.user_type == "System User")
			& user.name.notin(["Administrator", "Guest"])
		)
		.orderby(user.name)
	).run(pluck=True)


def has_balance_summary_since(user: str, since) -> bool:
	"""Whether the weekly balance summary was queued for `user` on or after `since` (LV-010, Q27)."""
	queue = frappe.qb.DocType("Email Queue")
	recipient = frappe.qb.DocType("Email Queue Recipient")
	return bool(
		(
			frappe.qb.from_(queue)
			.join(recipient)
			.on(recipient.parent == queue.name)
			.select(queue.name)
			.where(
				(queue.reference_doctype == "Nortix Leave Settings")
				& (queue.creation >= since)
				& (queue.status != "Error")
				& (recipient.recipient == user)
			)
			.limit(1)
		).run()
	)
