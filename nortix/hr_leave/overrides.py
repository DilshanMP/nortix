"""Leave Application changes for Saturday half days (LV-014).

Frappe HR removes every holiday in a leave as a whole day, so a Saturday half day would count
as no leave at all. These overrides count it as 0.5 in the form's live figure, the balance check
and the ledger entry made on submit. Frappe HR recounts days itself when a leave runs past its
allocation, so such a leave that includes a Saturday is refused and applied for per period.
"""

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate
from hrms.hr.doctype.leave_application.leave_application import (
	LeaveApplication,
	get_leave_balance_on,
	is_lwp,
)
from hrms.hr.doctype.leave_application.leave_application import (
	get_number_of_leave_days as hrms_get_number_of_leave_days,
)

from nortix.hr_leave.services import queries
from nortix.hr_leave.services.calendar import get_half_day_holidays, get_saturday_correction


@frappe.whitelist()
def get_number_of_leave_days(
	employee: str,
	leave_type: str,
	from_date,
	to_date,
	half_day=None,
	half_day_date=None,
	holiday_list: str | None = None,
	leave_application: str | None = None,
) -> float:
	days = hrms_get_number_of_leave_days(
		employee, leave_type, from_date, to_date, half_day, half_day_date, holiday_list, leave_application
	)
	# Leave types that include holidays never had them removed, so there is nothing to add back.
	if frappe.db.get_value("Leave Type", leave_type, "include_holiday"):
		return days
	return flt(days) + get_saturday_correction(
		from_date, to_date, half_day, half_day_date, get_half_day_holidays(employee, from_date, to_date)
	)


class NortixLeaveApplication(LeaveApplication):
	def validate_balance_leaves(self):
		"""Frappe HR's check with the Saturday-corrected day count (LV-014). Kept close to the
		original so an upgrade that changes it is caught by the LV-014 tests."""
		if not (self.from_date and self.to_date):
			return
		leave_application = None if self.is_new() else self.name
		self.validate_saturday_within_one_allocation()
		precision = cint(frappe.db.get_single_value("System Settings", "float_precision")) or 2
		self.total_leave_days = get_number_of_leave_days(
			self.employee,
			self.leave_type,
			self.from_date,
			self.to_date,
			self.half_day,
			self.half_day_date,
			leave_application=leave_application,
		)
		if self.total_leave_days <= 0:
			frappe.throw(
				_(
					"The day(s) on which you are applying for leave are holidays. You need not apply for leave."
				)
			)
		if is_lwp(self.leave_type):
			return
		leave_balance = get_leave_balance_on(
			self.employee,
			self.leave_type,
			self.from_date,
			self.to_date,
			consider_all_leaves_in_the_allocation_period=True,
			for_consumption=True,
			leave_application=leave_application,
		)
		available = flt(leave_balance.get("leave_balance_for_consumption"), precision)
		if self.status != "Rejected" and (available < self.total_leave_days or not available):
			self.show_insufficient_balance_message(available)

	def validate_saturday_within_one_allocation(self):
		"""LV-014: Frappe HR splits a leave that runs past its allocation with its own day count,
		which would take a Saturday as a whole day. The product owner chose to have such leave
		applied for separately in each period instead (2026-11-12)."""
		if frappe.db.get_value("Leave Type", self.leave_type, "include_holiday"):
			return
		allocation = queries.get_allocation_covering(self.employee, self.leave_type, self.from_date)
		if not allocation or getdate(allocation.to_date) >= getdate(self.to_date):
			return
		if get_half_day_holidays(self.employee, self.from_date, self.to_date):
			frappe.throw(
				_(
					"This leave runs past {0}, the end of the current leave allocation, and includes a Saturday. Please apply separately for the days up to {0} and the days after it."
				).format(frappe.format(allocation.to_date, "Date")),
				title=_("Apply for Each Period Separately"),
			)
