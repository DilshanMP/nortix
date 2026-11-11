"""Low and critical leave balance alerts (LV-010)."""

import frappe
from frappe import _
from frappe.utils import add_days, escape_html, flt, formatdate, getdate
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on

from nortix.hr_leave.services import queries

LEAVE_TYPE_FIELDS = ("casual_leave_type", "additional_leave_type", "annual_leave_type", "medical_leave_type")
EXCLUDED_RECIPIENT_ROLES = ("Employee", "Employee Self Service", "All", "Guest", "Desk User")
LOW = "Low"
CRITICAL = "Critical"


def classify_balance(balance: float, settings) -> str | None:
	"""LV-010: Critical at or below the critical threshold, Low at or below the low threshold."""
	if balance <= flt(settings.critical_balance_days):
		return CRITICAL
	if balance <= flt(settings.low_balance_days):
		return LOW
	return None


def validate_alert_settings(settings) -> None:
	"""LV-010, LV-011: thresholds must be ordered and an enabled summary needs a recipient role."""
	low, critical = flt(settings.low_balance_days), flt(settings.critical_balance_days)
	if critical < 0 or low > 366 or critical > low:
		frappe.throw(
			_(
				"The critical balance must be at least 0 and no more than the low balance, which must be at most 366 days."
			),
			title=_("Invalid Balance Thresholds"),
		)
	if settings.is_balance_alert_enabled and not settings.balance_alert_role:
		frappe.throw(
			_("Set the role that receives the weekly summary before turning it on."),
			title=_("Recipient Role Missing"),
		)
	if settings.balance_alert_role and not is_hr_role(settings.balance_alert_role):
		frappe.throw(
			_(
				"Role {0} cannot receive the weekly summary: the recipient role must be able to read every Leave Allocation it is allowed to see, as HR roles can. Employee roles would expose other people's balances."
			).format(frappe.bold(settings.balance_alert_role)),
			title=_("Recipient Role Not Allowed"),
		)


def is_hr_role(role: str) -> bool:
	"""A role that reads Leave Allocations in general, not only its own (LV-010, T5).

	The Employee roles can read Employee records broadly when no User Permission limits them,
	so letting them receive the summary would email other people's balances to ordinary staff.
	"""
	if role in EXCLUDED_RECIPIENT_ROLES:
		return False
	return any(
		perm.role == role and perm.read and not perm.if_owner and not perm.permlevel
		for perm in frappe.get_meta("Leave Allocation").permissions
	)


def get_balance_alerts(on_date=None, user: str | None = None, company: str | None = None) -> list[dict]:
	"""LV-010: Active employees whose balance for a configured leave type is low or critical on
	`on_date`, limited to the employees `user` may read (LV-012).

	Only leave types the employee has an allocation for on that date are checked, so an
	employee before their 1-year mark is not flagged for annual leave they do not have yet.
	"""
	on_date = getdate(on_date)
	settings = frappe.get_single("Nortix Leave Settings")
	leave_types = sorted(
		{settings.get(fieldname) for fieldname in LEAVE_TYPE_FIELDS if settings.get(fieldname)}
	)
	if not leave_types:
		return []

	filters = {"status": "Active"}
	if company:
		filters["company"] = company
	employees = frappe.get_list(
		"Employee",
		filters=filters,
		fields=["name", "employee_name", "company"],
		order_by="name",
		user=user,
	)
	if not employees:
		return []

	allocated = queries.get_allocated_leave_types(
		[employee.name for employee in employees], leave_types, on_date
	)
	rows = []
	for employee in employees:
		for leave_type in leave_types:
			if (employee.name, leave_type) not in allocated:
				continue
			balance = flt(
				get_leave_balance_on(
					employee.name, leave_type, on_date, consider_all_leaves_in_the_allocation_period=True
				)
			)
			level = classify_balance(balance, settings)
			if level:
				rows.append(
					{
						"employee": employee.name,
						"employee_name": employee.employee_name,
						"company": employee.company,
						"leave_type": leave_type,
						"balance": balance,
						"level": level,
					}
				)
	return rows


def send_weekly_alerts(on_date=None) -> list[str]:
	"""LV-010: email each holder of the recipient role a summary of the low and critical balances
	they are allowed to see; returns the users emailed.

	Balances are worked out once, then each recipient's list is cut down to the employees their
	own permissions allow (LV-012). A recipient with no Company restriction would receive every
	company, so they are included only when the settings say so (Q26). Each recipient gets at most
	one summary per week, so a re-run or retry does not email them again (Q27).
	"""
	settings = frappe.get_single("Nortix Leave Settings")
	if not settings.is_balance_alert_enabled or not settings.balance_alert_role:
		return []

	on_date = getdate(on_date)
	all_rows = get_balance_alerts(on_date)
	if not all_rows:
		return []

	week_start = add_days(on_date, -on_date.weekday())
	sent = []
	for user in queries.get_enabled_users_with_role(settings.balance_alert_role):
		if not settings.is_balance_alert_to_unrestricted and not has_company_restriction(user):
			continue
		if queries.has_balance_summary_since(user, week_start):
			continue
		try:
			visible = _employees_visible_to(user)
			rows = [row for row in all_rows if row["employee"] in visible]
			if not rows:
				continue
			frappe.sendmail(
				recipients=[user],
				subject=_("Leave balances to check, {0}").format(formatdate(on_date)),
				message=_render_summary(rows, on_date),
				reference_doctype="Nortix Leave Settings",
				reference_name="Nortix Leave Settings",
			)
		except Exception as error:
			# One recipient's problem must not stop the others; log IDs and the error type only.
			frappe.log_error(
				title="Leave balance summary not sent",
				message=f"{type(error).__name__} for user {user}",
				reference_doctype="Nortix Leave Settings",
			)
			continue
		sent.append(user)
	return sent


def has_company_restriction(user: str) -> bool:
	return bool(frappe.permissions.get_user_permissions(user).get("Company"))


def _employees_visible_to(user: str) -> set[str]:
	return set(frappe.get_list("Employee", filters={"status": "Active"}, pluck="name", user=user))


def _render_summary(rows: list[dict], on_date) -> str:
	header = "".join(
		f"<th>{escape_html(_(label))}</th>"
		for label in ("Employee", "Name", "Company", "Leave Type", "Balance", "Level")
	)
	body = "".join(
		"<tr>"
		+ "".join(
			f"<td>{escape_html(str(row[key]))}</td>"
			for key in ("employee", "employee_name", "company", "leave_type", "balance", "level")
		)
		+ "</tr>"
		for row in sorted(rows, key=lambda row: (row["level"] != CRITICAL, row["company"], row["employee"]))
	)
	intro = escape_html(
		_("Employees with a low or critical leave balance on {0}.").format(formatdate(on_date))
	)
	return f"<p>{intro}</p><table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table>"
