"""Casual, additional and medical leave entitlements (LV-003, LV-004, LV-005, LV-007)."""

from dataclasses import dataclass
from datetime import date

from frappe.utils import add_days, flt, getdate

from nortix.hr_leave.services.annual import get_mark_date


@dataclass(frozen=True)
class Entitlement:
	from_date: date
	to_date: date
	days: float


def get_casual_entitlement(join_date, period_from, period_to, on_date, settings) -> Entitlement | None:
	"""LV-003, LV-004: casual leave due for one leave period on `on_date`.

	Joining year: the monthly amount for each month from the join month to December, up front
	from the join date (Q3). Later years: the before-mark amount, rising to the after-mark amount
	from the mark date; casual leave already taken counts against it.
	"""
	join_date, period_from, period_to, on_date = (
		getdate(join_date),
		getdate(period_from),
		getdate(period_to),
		getdate(on_date),
	)
	start = max(join_date, period_from)
	if start > on_date or join_date > period_to:
		return None

	if join_date >= period_from:
		days = flt(settings.casual_monthly_days_first_year) * (13 - join_date.month)
	elif get_mark_date(join_date) <= on_date:
		days = flt(settings.casual_days_after_mark)
	else:
		days = flt(settings.casual_days_before_mark)
	return _entitlement(start, period_to, days)


def get_additional_entitlement(join_date, period_from, period_to, on_date, settings) -> Entitlement | None:
	"""LV-005: the additional day for each period before the mark, usable until the day before
	the mark (Q18, Q19); nothing once the mark is reached."""
	join_date, period_from, period_to, on_date = (
		getdate(join_date),
		getdate(period_from),
		getdate(period_to),
		getdate(on_date),
	)
	mark = get_mark_date(join_date)
	start = max(join_date, period_from)
	end = min(period_to, getdate(add_days(mark, -1)))
	if start > on_date or start > end or on_date >= mark:
		return None
	return _entitlement(start, end, flt(settings.additional_days_before_mark))


def get_medical_entitlement(join_date, period_from, period_to, on_date, settings) -> Entitlement | None:
	"""LV-007: the medical amount for the period from joining, in full in the joining year (Q20)."""
	join_date, period_from, period_to, on_date = (
		getdate(join_date),
		getdate(period_from),
		getdate(period_to),
		getdate(on_date),
	)
	start = max(join_date, period_from)
	if start > on_date or join_date > period_to:
		return None
	return _entitlement(start, period_to, flt(settings.medical_days))


def _entitlement(from_date: date, to_date: date, days: float) -> Entitlement | None:
	if days <= 0:
		return None
	return Entitlement(from_date=from_date, to_date=to_date, days=days)
