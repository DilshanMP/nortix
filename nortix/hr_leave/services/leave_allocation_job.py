"""Daily allocation of casual, additional and medical leave (LV-003, LV-004, LV-005, LV-007)."""

from collections.abc import Callable
from dataclasses import dataclass

import frappe
from frappe import _
from frappe.utils import flt, getdate
from frappe.utils.file_lock import LockTimeoutError
from frappe.utils.synchronization import filelock

from nortix.hr_leave.services import queries
from nortix.hr_leave.services.allocation_source import allow_allocation_source
from nortix.hr_leave.services.annual import MAX_DAYS, get_mark_date, is_calendar_year
from nortix.hr_leave.services.leave_rules import (
	Entitlement,
	get_additional_entitlement,
	get_casual_entitlement,
	get_medical_entitlement,
)

RUN_LOCK = "nortix_leave_allocation"


@dataclass(frozen=True)
class LeaveRule:
	name: str
	switch_field: str
	leave_type_field: str
	source: str
	amount_fields: tuple[str, ...]
	entitlement: Callable[..., Entitlement | None]
	# A medical allocation for a December joiner holds more days than remain in the period.
	requires_over_allocation: bool = False

	def largest_allocation(self, settings) -> float:
		if self.name == "casual":
			return max(
				flt(settings.casual_monthly_days_first_year) * 12,
				flt(settings.casual_days_before_mark),
				flt(settings.casual_days_after_mark),
			)
		return max(flt(settings.get(fieldname)) for fieldname in self.amount_fields)


RULES = (
	LeaveRule(
		"casual",
		"is_casual_allocation_enabled",
		"casual_leave_type",
		"casual_rule",
		("casual_monthly_days_first_year", "casual_days_before_mark", "casual_days_after_mark"),
		get_casual_entitlement,
	),
	LeaveRule(
		"additional",
		"is_additional_allocation_enabled",
		"additional_leave_type",
		"additional_rule",
		("additional_days_before_mark",),
		get_additional_entitlement,
	),
	LeaveRule(
		"medical",
		"is_medical_allocation_enabled",
		"medical_leave_type",
		"medical_rule",
		("medical_days",),
		get_medical_entitlement,
		requires_over_allocation=True,
	),
)


def validate_leave_settings(settings) -> None:
	"""LV-011: reject casual, additional and medical settings the daily job could not apply."""
	for rule in RULES:
		for fieldname in rule.amount_fields:
			value = flt(settings.get(fieldname))
			if value < 0 or value > MAX_DAYS:
				frappe.throw(
					_("{0} must be between 0 and {1} days.").format(
						_(settings.meta.get_label(fieldname)), MAX_DAYS
					),
					title=_("Invalid Leave Days"),
				)
		if not settings.get(rule.switch_field):
			continue
		if not settings.get(rule.leave_type_field):
			frappe.throw(
				_("Set the {0} before turning on its automatic allocation.").format(
					_(settings.meta.get_label(rule.leave_type_field))
				),
				title=_("Leave Type Missing"),
			)
		validate_rule_leave_type(settings, rule)


def validate_rule_leave_type(settings, rule: LeaveRule) -> None:
	name = settings.get(rule.leave_type_field)
	leave_type = frappe.db.get_value(
		"Leave Type",
		name,
		["allow_over_allocation", "is_earned_leave", "is_carry_forward", "max_leaves_allowed"],
		as_dict=True,
	)
	if not leave_type:
		frappe.throw(
			_("Leave Type {0} does not exist.").format(frappe.bold(name)), title=_("Leave Type Not Found")
		)
	if leave_type.is_earned_leave or leave_type.is_carry_forward:
		frappe.throw(
			_(
				"Leave Type {0} must not be earned leave or carry-forward leave; it is granted by the leave rules and does not carry forward."
			).format(frappe.bold(name)),
			title=_("Leave Type Not Suitable"),
		)
	if rule.requires_over_allocation and not leave_type.allow_over_allocation:
		frappe.throw(
			_(
				"Leave Type {0} must allow over allocation, because an employee who joins near the end of a leave period receives more days than remain in it."
			).format(frappe.bold(name)),
			title=_("Leave Type Not Suitable"),
		)
	largest = rule.largest_allocation(settings)
	if leave_type.max_leaves_allowed and flt(leave_type.max_leaves_allowed) < largest:
		frappe.throw(
			_("Leave Type {0} allows at most {1} days, but the leave settings grant up to {2}.").format(
				frappe.bold(name), leave_type.max_leaves_allowed, largest
			),
			title=_("Leave Type Not Suitable"),
		)


def allocate_due_leave(on_date=None) -> dict:
	"""LV-003, LV-004, LV-005, LV-007: create and submit the casual, additional and medical
	allocations due on `on_date`, and add the extra casual day at the 1-year mark.

	Safe to run any number of times: an employee already handled for a leave type and period is
	skipped, a cancelled allocation or adjustment made by the job is not recreated, and a second
	run started while one is in progress stops at the lock.
	"""
	summary = {
		"created": [],
		"adjusted": [],
		"skipped": [],
		"failed": [],
		"companies_without_period": [],
		"periods_not_calendar_year": [],
		"not_run": [],
	}
	try:
		with filelock(RUN_LOCK, timeout=1):
			_allocate(getdate(on_date), summary)
	except LockTimeoutError:
		summary["not_run"].append("already running")
	return summary


def _allocate(on_date, summary: dict) -> None:
	settings = frappe.get_single("Nortix Leave Settings")
	rules = []
	for rule in RULES:
		if not settings.get(rule.switch_field) or not settings.get(rule.leave_type_field):
			continue
		try:
			validate_rule_leave_type(settings, rule)
		except frappe.ValidationError:
			frappe.log_error(
				title="Leave allocation not run",
				message=f"The {rule.name} leave type is missing or no longer suitable; check Nortix Leave Settings.",
				reference_doctype="Nortix Leave Settings",
			)
			summary["not_run"].append(f"{rule.name} leave type not suitable")
			continue
		rules.append(rule)
	if not rules:
		return

	periods = queries.get_active_leave_periods(on_date)
	companies_with_period = {period.company for period in periods}
	summary["companies_without_period"] = sorted(
		set(queries.get_companies_with_active_employees()) - companies_with_period
	)
	summary["periods_not_calendar_year"] = [period.name for period in periods if not is_calendar_year(period)]

	for period in (period for period in periods if is_calendar_year(period)):
		employees = queries.get_active_employees_joined_by(period.company, on_date)
		names = [employee.name for employee in employees]
		for rule in rules:
			leave_type = settings.get(rule.leave_type_field)
			handled = queries.get_employees_with_annual_allocation(
				names, leave_type, period.from_date, period.to_date, rule.source
			)
			for employee in employees:
				if employee.name in handled:
					if rule.name == "casual":
						_run_safely(
							summary,
							employee,
							period,
							_top_up_casual,
							employee,
							period,
							leave_type,
							settings,
							on_date,
						)
					else:
						summary["skipped"].append(employee.name)
					continue
				entitlement = rule.entitlement(
					employee.date_of_joining, period.from_date, period.to_date, on_date, settings
				)
				if not entitlement:
					continue
				_run_safely(
					summary,
					employee,
					period,
					_create_allocation,
					employee,
					period,
					leave_type,
					rule,
					entitlement,
				)


def _run_safely(summary: dict, employee, period, action, *args) -> None:
	frappe.db.savepoint("nortix_leave_allocation")
	try:
		action(*args, summary=summary)
	except Exception as error:
		frappe.db.rollback(save_point="nortix_leave_allocation")
		# Leave Allocation messages can carry employee details, so only IDs and the error type
		# are logged.
		frappe.log_error(
			title="Leave allocation failed",
			message=f"{type(error).__name__} for employee {employee.name}, leave period {period.name}",
			reference_doctype="Employee",
			reference_name=employee.name,
		)
		summary["failed"].append(employee.name)


def _create_allocation(
	employee, period, leave_type: str, rule: LeaveRule, entitlement: Entitlement, summary
) -> None:
	allocation = frappe.get_doc(
		{
			"doctype": "Leave Allocation",
			"employee": employee.name,
			"company": period.company,
			"leave_type": leave_type,
			"leave_period": period.name,
			"from_date": entitlement.from_date,
			"to_date": entitlement.to_date,
			"new_leaves_allocated": entitlement.days,
			"nortix_source": rule.source,
			"description": _("Allocated by the {0} leave rule").format(_(rule.name)),
		}
	)
	with allow_allocation_source():
		allocation.insert()
		allocation.submit()
	summary["created"].append(allocation.name)


def _top_up_casual(employee, period, leave_type: str, settings, on_date, summary) -> None:
	"""LV-004: in the year of the mark, add the difference between the after-mark and
	before-mark casual amounts on the mark date, once per allocation."""
	allocation = queries.get_rule_allocation(
		employee.name, leave_type, period.from_date, period.to_date, "casual_rule"
	)
	entitlement = get_casual_entitlement(
		employee.date_of_joining, period.from_date, period.to_date, on_date, settings
	)
	missing = entitlement and allocation and entitlement.days - flt(allocation.total_leaves_allocated)
	# Any adjustment, even one HR cancelled, means the top-up was already handled.
	if not missing or missing <= 0 or queries.has_leave_adjustment(allocation.name):
		summary["skipped"].append(employee.name)
		return

	adjustment = frappe.get_doc(
		{
			"doctype": "Leave Adjustment",
			"employee": employee.name,
			"leave_type": leave_type,
			"leave_allocation": allocation.name,
			"adjustment_type": "Allocate",
			"leaves_to_adjust": missing,
			"posting_date": max(get_mark_date(employee.date_of_joining), getdate(allocation.from_date)),
			"reason_for_adjustment": _("Casual leave from the 1-year mark"),
		}
	)
	adjustment.insert()
	adjustment.submit()
	summary["adjusted"].append(adjustment.name)
