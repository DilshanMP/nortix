"""Annual leave by quarter of the 1-year mark (LV-006)."""

from dataclasses import dataclass
from datetime import date

import frappe
from frappe import _
from frappe.utils import add_months, flt, getdate
from frappe.utils.file_lock import LockTimeoutError
from frappe.utils.synchronization import filelock

from nortix.hr_leave.services import queries
from nortix.hr_leave.services.allocation_source import allow_allocation_source

ALLOCATION_SOURCE = "annual_rule"
AMOUNT_FIELDS = ("annual_q1_days", "annual_q2_days", "annual_q3_days", "annual_q4_days", "annual_full_days")
MAX_DAYS = 366
RUN_LOCK = "nortix_annual_leave_allocation"


@dataclass(frozen=True)
class AnnualEntitlement:
	from_date: date
	days: float


def get_mark_date(join_date) -> date:
	"""LV-006, Q9, Q10: the anniversary of joining; a 29 February join date gives 28 February."""
	return getdate(add_months(getdate(join_date), 12))


def get_annual_entitlement(join_date, period_from, period_to, on_date, settings) -> AnnualEntitlement | None:
	"""LV-006: the annual allocation due on `on_date` for one leave period, or None.

	In the period of the mark the amount follows the mark's quarter and starts on the mark date
	(Q11); in later periods the full amount starts with the period.
	"""
	mark = get_mark_date(join_date)
	period_from, period_to, on_date = getdate(period_from), getdate(period_to), getdate(on_date)
	if mark > on_date or mark > period_to:
		return None

	if mark < period_from:
		from_date, days = period_from, flt(settings.annual_full_days)
	else:
		quarter = (mark.month - 1) // 3 + 1
		from_date, days = mark, flt(settings.get(f"annual_q{quarter}_days"))

	if days <= 0:
		return None
	return AnnualEntitlement(from_date=from_date, days=days)


def validate_annual_settings(settings) -> None:
	"""LV-006, LV-011: reject settings the daily job could not apply safely."""
	for fieldname in AMOUNT_FIELDS:
		value = flt(settings.get(fieldname))
		if value < 0 or value > MAX_DAYS:
			frappe.throw(
				_("{0} must be between 0 and {1} days.").format(
					_(settings.meta.get_label(fieldname)), MAX_DAYS
				),
				title=_("Invalid Annual Leave Days"),
			)

	if not settings.is_annual_allocation_enabled:
		return

	if not settings.annual_leave_type:
		frappe.throw(
			_("Set the Annual Leave Type before turning on automatic annual leave allocation."),
			title=_("Annual Leave Type Missing"),
		)

	validate_annual_leave_type(settings)


def validate_annual_leave_type(settings) -> None:
	"""LV-006: the annual Leave Type must exist and suit the quarter rule. Checked on save and
	again before every run, because the Leave Type can be edited after the settings are saved."""
	leave_type = frappe.db.get_value(
		"Leave Type",
		settings.annual_leave_type,
		["allow_over_allocation", "is_earned_leave", "is_carry_forward", "max_leaves_allowed"],
		as_dict=True,
	)
	if not leave_type:
		frappe.throw(
			_("Leave Type {0} does not exist.").format(frappe.bold(settings.annual_leave_type)),
			title=_("Leave Type Not Found"),
		)
	# A mark in the last days of a period gives more days than remain in it, which
	# Leave Allocation rejects unless the leave type allows over allocation.
	if not leave_type.allow_over_allocation:
		frappe.throw(
			_(
				"Leave Type {0} must allow over allocation, because an employee whose 1-year mark falls near the end of a leave period receives more days than remain in it."
			).format(frappe.bold(settings.annual_leave_type)),
			title=_("Leave Type Not Suitable"),
		)
	if leave_type.is_earned_leave or leave_type.is_carry_forward:
		frappe.throw(
			_(
				"Leave Type {0} must not be earned leave or carry-forward leave; annual leave is granted in full and does not carry forward."
			).format(frappe.bold(settings.annual_leave_type)),
			title=_("Leave Type Not Suitable"),
		)
	largest = max(flt(settings.get(fieldname)) for fieldname in AMOUNT_FIELDS)
	if leave_type.max_leaves_allowed and flt(leave_type.max_leaves_allowed) < largest:
		frappe.throw(
			_(
				"Leave Type {0} allows at most {1} days, but the annual leave settings grant up to {2}."
			).format(frappe.bold(settings.annual_leave_type), leave_type.max_leaves_allowed, largest),
			title=_("Leave Type Not Suitable"),
		)


def allocate_due_annual_leave(on_date=None) -> dict:
	"""LV-006: create and submit the annual allocation for every employee whose entitlement has started.

	Safe to run any number of times: an employee already handled for the period is skipped (Q16),
	and a second run started while one is in progress stops at the lock. A failure for one
	employee is logged and does not stop the others.
	"""
	summary = {
		"created": [],
		"skipped": [],
		"failed": [],
		"companies_without_period": [],
		"periods_not_calendar_year": [],
		"not_run": None,
	}
	try:
		with filelock(RUN_LOCK, timeout=1):
			_allocate(getdate(on_date), summary)
	except LockTimeoutError:
		summary["not_run"] = "already running"
	return summary


def _allocate(on_date, summary: dict) -> None:
	settings = frappe.get_single("Nortix Leave Settings")
	leave_type = settings.annual_leave_type
	if not leave_type:
		summary["not_run"] = "no annual leave type"
		return
	try:
		validate_annual_leave_type(settings)
	except frappe.ValidationError:
		frappe.log_error(
			title="Annual leave allocation not run",
			message=f"Leave Type {leave_type} is missing or no longer suitable; check Nortix Leave Settings.",
			reference_doctype="Nortix Leave Settings",
		)
		summary["not_run"] = "annual leave type not suitable"
		return

	periods = queries.get_active_leave_periods(on_date)
	companies_with_period = {period.company for period in periods}
	summary["companies_without_period"] = sorted(
		set(queries.get_companies_with_active_employees()) - companies_with_period
	)
	# Every amount assumes the calendar year (LV-002); another period shape is reported, not guessed.
	summary["periods_not_calendar_year"] = [
		period.name for period in periods if not _is_calendar_year(period)
	]
	periods = [period for period in periods if _is_calendar_year(period)]

	for period in periods:
		employees = queries.get_active_employees_joined_by(period.company, on_date)
		handled = queries.get_employees_with_annual_allocation(
			[employee.name for employee in employees],
			leave_type,
			period.from_date,
			period.to_date,
			ALLOCATION_SOURCE,
		)
		for employee in employees:
			if employee.name in handled:
				summary["skipped"].append(employee.name)
				continue
			entitlement = get_annual_entitlement(
				employee.date_of_joining, period.from_date, period.to_date, on_date, settings
			)
			if not entitlement:
				continue
			frappe.db.savepoint("nortix_annual_allocation")
			try:
				summary["created"].append(_create_allocation(employee, period, leave_type, entitlement))
			except Exception as error:
				frappe.db.rollback(save_point="nortix_annual_allocation")
				# Leave Allocation messages can carry employee details, so only IDs and the
				# error type are logged.
				frappe.log_error(
					title="Annual leave allocation failed",
					message=f"{type(error).__name__} for employee {employee.name}, leave period {period.name}",
					reference_doctype="Employee",
					reference_name=employee.name,
				)
				summary["failed"].append(employee.name)


def _is_calendar_year(period) -> bool:
	from_date, to_date = getdate(period.from_date), getdate(period.to_date)
	return (from_date.month, from_date.day) == (1, 1) and to_date == date(from_date.year, 12, 31)


def _create_allocation(employee, period, leave_type: str, entitlement: AnnualEntitlement) -> str:
	allocation = frappe.get_doc(
		{
			"doctype": "Leave Allocation",
			"employee": employee.name,
			"company": period.company,
			"leave_type": leave_type,
			"leave_period": period.name,
			"from_date": entitlement.from_date,
			"to_date": period.to_date,
			"new_leaves_allocated": entitlement.days,
			"nortix_source": ALLOCATION_SOURCE,
			"description": _("Annual leave by quarter of the 1-year mark"),
		}
	)
	with allow_allocation_source():
		allocation.insert()
		allocation.submit()
	return allocation.name
