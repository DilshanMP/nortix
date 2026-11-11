"""Yearly holiday calendar with Saturday half days (LV-014)."""

from datetime import date, timedelta

import frappe
from frappe import _
from frappe.utils import cint, getdate
from hrms.utils.holiday_list import get_holiday_dates_between, get_holiday_list_ranges_for_employee

SATURDAY, SUNDAY = 5, 6


def holiday_list_name(year: int) -> str:
	return f"Nortix {cint(year)}"


def get_calendar_rows(year: int, mercantile_holidays: list[dict]) -> list[dict]:
	"""LV-014: every Sunday off, every Saturday a half day, each mercantile holiday a full day.

	A mercantile holiday on a Saturday replaces that half day with a full day; one on a Sunday
	keeps the single Sunday row with the holiday's name.
	"""
	year = cint(year)
	rows = {}
	day = date(year, 1, 1)
	while day.year == year:
		if day.weekday() == SUNDAY:
			rows[day] = {"holiday_date": day, "weekly_off": 1, "is_half_day": 0, "description": _("Sunday")}
		elif day.weekday() == SATURDAY:
			rows[day] = {
				"holiday_date": day,
				"weekly_off": 1,
				"is_half_day": 1,
				"description": _("Saturday (half day)"),
			}
		day += timedelta(days=1)

	for holiday in mercantile_holidays:
		holiday_date = getdate(holiday["holiday_date"])
		if holiday_date.year != year:
			continue
		row = rows.setdefault(holiday_date, {"holiday_date": holiday_date, "weekly_off": 0})
		row.update({"is_half_day": 0, "description": holiday["description"]})
		if holiday_date.weekday() == SATURDAY:
			row["weekly_off"] = 0

	return [rows[key] for key in sorted(rows)]


def get_saturday_correction(from_date, to_date, half_day, half_day_date, half_day_holidays) -> float:
	"""LV-014, Q28: Frappe HR removes every holiday in a leave as a whole day; a Saturday half day
	should count 0.5, so add 0.5 back for each. A half-day request on a Saturday also counts 0.5
	in total, so it gets the half day Frappe HR took off back as well."""
	from_date, to_date = getdate(from_date), getdate(to_date)
	saturdays = {getdate(day) for day in half_day_holidays if from_date <= getdate(day) <= to_date}
	correction = 0.5 * len(saturdays)
	if cint(half_day):
		requested_half = getdate(half_day_date) if half_day_date else from_date
		if from_date == to_date:
			requested_half = from_date
		if requested_half in saturdays:
			correction += 0.5
	return correction


def get_half_day_holidays(employee: str, from_date, to_date) -> list:
	"""Half-day holidays in the employee's holiday lists between the dates."""
	dates = []
	for holiday_range in get_holiday_list_ranges_for_employee(
		employee, from_date, to_date, raise_exception=False
	):
		dates += get_holiday_dates_between(
			holiday_range.holiday_list,
			max(getdate(from_date), getdate(holiday_range.from_date)),
			min(getdate(to_date), getdate(holiday_range.to_date)),
			only_half_days=True,
		)
	return dates


def build_calendar(year: int, log_conflicts: bool = True) -> str | None:
	"""LV-014, Q29: create or refresh the year's Holiday List from the mercantile holidays HR
	entered, and assign it to every company. Safe to run again: the rows are replaced, and a
	company already assigned is not assigned twice. Returns the list name, or None when a Holiday
	List of that name exists that this calendar did not create (it is never overwritten)."""
	year = cint(year)
	holiday_year = frappe.db.get_value(
		"Nortix Holiday Year", {"year": year}, ["name", "holiday_list"], as_dict=True
	)
	name = holiday_list_name(year)
	exists = frappe.db.exists("Holiday List", name)
	if exists and not (holiday_year and holiday_year.holiday_list == name):
		frappe.log_error(
			title="Holiday calendar needs review",
			message=f"A Holiday List named {name} already exists and was not created by the yearly calendar; "
			"it was left unchanged. Rename it so the calendar can be built.",
			reference_doctype="Nortix Holiday Year",
		)
		return None

	holidays = (
		frappe.get_all(
			"Nortix Mercantile Holiday",
			filters={"parent": holiday_year.name, "parenttype": "Nortix Holiday Year"},
			fields=["holiday_date", "description"],
		)
		if holiday_year
		else []
	)
	holiday_list = frappe.get_doc("Holiday List", name) if exists else frappe.new_doc("Holiday List")
	holiday_list.update(
		{
			"holiday_list_name": name,
			"from_date": date(year, 1, 1),
			"to_date": date(year, 12, 31),
			"weekly_off": None,
		}
	)
	holiday_list.set("holidays", get_calendar_rows(year, holidays))
	# Only group-wide HR may maintain the calendar (LV-014); Holiday List itself is derived from
	# their entries, so the system writes it on their behalf.
	holiday_list.flags.ignore_permissions = True
	holiday_list.save()

	if holiday_year:
		frappe.db.set_value(
			"Nortix Holiday Year", holiday_year.name, "holiday_list", name, update_modified=False
		)
	assign_to_companies(year, log_conflicts=log_conflicts)
	return name


def assign_to_companies(year: int, log_conflicts: bool = True) -> dict:
	"""Give every company the year's calendar from 1 January (Q29).

	A company whose own calendar already covers part of the year is left alone and reported for
	HR: replacing it would silently change how its leave is counted.
	Returns {"added": [...], "conflicts": [...]}.
	"""
	year = cint(year)
	name = holiday_list_name(year)
	start, end = date(year, 1, 1), date(year, 12, 31)
	assignment = frappe.qb.DocType("Holiday List Assignment")
	holiday_list = frappe.qb.DocType("Holiday List")
	rows = (
		frappe.qb.from_(assignment)
		.join(holiday_list)
		.on(holiday_list.name == assignment.holiday_list)
		.select(assignment.assigned_to, assignment.holiday_list)
		.where(
			(assignment.applicable_for == "Company")
			& (assignment.docstatus == 1)
			& (assignment.from_date <= end)
			& (holiday_list.to_date >= start)
		)
	).run(as_dict=True)
	assigned, competing = set(), set()
	for row in rows:
		(assigned if row.holiday_list == name else competing).add(row.assigned_to)

	result = {"added": [], "conflicts": sorted(competing - assigned)}
	for company in frappe.get_all("Company", pluck="name"):
		if company in assigned or company in competing:
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Holiday List Assignment",
				"applicable_for": "Company",
				"assigned_to": company,
				"holiday_list": name,
				"from_date": start,
			}
		)
		doc.flags.ignore_permissions = True
		doc.insert()
		doc.submit()
		result["added"].append(company)
	if result["conflicts"] and log_conflicts:
		frappe.log_error(
			title="Holiday calendar needs review",
			message=f"{name} was not assigned because these companies already have another calendar "
			f"covering {year}: " + ", ".join(result["conflicts"]),
			reference_doctype="Nortix Holiday Year",
		)
	return result


def ensure_calendars(on_date) -> list[int]:
	"""LV-014: make sure this year's calendar exists, and next year's from 1 December, so leave
	can be counted before HR enters the mercantile holidays, and that companies added since are
	assigned. Conflicts are reported when HR saves the year, not every day. Returns the years
	created."""
	on_date = getdate(on_date)
	years = [on_date.year] + ([on_date.year + 1] if on_date.month == 12 else [])
	created = []
	for year in years:
		if frappe.db.exists("Nortix Holiday Year", {"year": year}):
			if frappe.db.exists("Holiday List", holiday_list_name(year)):
				assign_to_companies(year, log_conflicts=False)
			continue
		doc = frappe.get_doc({"doctype": "Nortix Holiday Year", "year": year})
		doc.flags.ignore_permissions = True
		doc.flags.from_daily_job = True
		doc.insert()
		created.append(year)
	return created
