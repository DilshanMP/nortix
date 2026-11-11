"""Medical leave approval by HR and named backups (LV-007, LV-009, Q23, Q30, Q32)."""

import frappe
from frappe import _
from frappe.utils import escape_html, formatdate, get_fullname
from hrms.hr.doctype.leave_application.leave_application import get_employee_leave_approver

from nortix.hr_leave.services import queries

HR_ROLES = ("HR Manager", "HR User")
DECIDING_ROLES = {"Leave Approver", *HR_ROLES}
DECISIONS = ("Approved", "Rejected")


def _settings():
	# Read fresh: a cached copy can outlive a settings change or a rolled-back transaction.
	return frappe.get_single("Nortix Leave Settings")


def _is_medical(doc, settings) -> bool:
	return bool(settings.medical_leave_type) and doc.leave_type == settings.medical_leave_type


def _backups(settings) -> set[str]:
	return {row.user for row in settings.medical_backup_approvers or []}


def _roles(user: str) -> set[str]:
	return set(frappe.get_roles(user))


def _is_hr(user: str) -> bool:
	return bool(_roles(user) & set(HR_ROLES))


def _is_enabled(user: str) -> bool:
	return bool(frappe.db.get_value("User", user, "enabled"))


def _can_see_application(user: str, doc) -> bool:
	"""Whether the user's own permission rules (company, employee) allow this application (Q30).
	Backups reach applications through the Leave Approver role, limited by these rules; nothing is
	shared with them, because a Frappe share that allows submit always allows editing too."""
	return frappe.permissions.has_user_permission(doc, user=user)


def _is_active_backup(user: str, settings) -> bool:
	"""A named backup who is still enabled and still holds a role that can decide leave."""
	return user in _backups(settings) and _is_enabled(user) and bool(_roles(user) & DECIDING_ROLES)


def validate_medical_settings(settings) -> None:
	"""Q23, Q30: the named approver is a group-wide HR user, because every company's medical
	applications go to them; backups must be active users who can decide leave."""
	approver = settings.medical_leave_approver
	if approver:
		if not _is_hr(approver) or not _is_enabled(approver):
			frappe.throw(
				_(
					"The Medical Leave Approver {0} must be an enabled user with the HR Manager or HR User role."
				).format(frappe.bold(approver)),
				title=_("Approver Not HR"),
			)
		if frappe.permissions.get_user_permissions(approver).get("Company"):
			frappe.throw(
				_(
					"The Medical Leave Approver {0} is limited to certain companies, but receives every company's medical applications. Choose a group-wide HR user."
				).format(frappe.bold(approver)),
				title=_("Approver Not Group-Wide"),
			)
	for row in settings.medical_backup_approvers or []:
		enabled, user_type = frappe.db.get_value("User", row.user, ["enabled", "user_type"]) or (0, None)
		if not enabled or user_type != "System User":
			frappe.throw(
				_("Backup approver {0} must be an enabled system user.").format(frappe.bold(row.user)),
				title=_("Backup Approver Not Allowed"),
			)
		# Frappe HR lets only Leave Approver and HR roles change an application's status.
		if not _roles(row.user) & DECIDING_ROLES:
			frappe.throw(
				_("Backup approver {0} needs the Leave Approver role to approve or reject leave.").format(
					frappe.bold(row.user)
				),
				title=_("Backup Approver Not Allowed"),
			)


def route_to_hr(doc, method=None) -> None:
	"""LV-007: a draft medical application goes to the named HR user; one changed away from
	medical goes back to the employee's usual approver."""
	if doc.docstatus:
		return
	settings = _settings()
	approver = settings.medical_leave_approver
	if _is_medical(doc, settings):
		if approver and doc.leave_approver != approver:
			doc.leave_approver = approver
			doc.leave_approver_name = get_fullname(approver)
	elif approver and doc.leave_approver == approver and doc.has_value_changed("leave_type"):
		doc.leave_approver = get_employee_leave_approver(doc.employee)
		doc.leave_approver_name = get_fullname(doc.leave_approver) if doc.leave_approver else None


def check_approver(doc, method=None) -> None:
	"""LV-007, LV-009, Q30: medical leave is decided only by HR or an active named backup who
	can see the employee, and never by the employee themselves. Applies to the form and the API
	alike, because both submit the document."""
	settings = _settings()
	if not _is_medical(doc, settings) or doc.status not in DECISIONS:
		return
	user = frappe.session.user
	if user == frappe.db.get_value("Employee", doc.employee, "user_id"):
		frappe.throw(_("You cannot decide your own medical leave."), frappe.PermissionError)
	if user == "Administrator":
		return
	allowed = _is_hr(user) or _is_active_backup(user, settings)
	if not allowed or not _can_see_application(user, doc):
		frappe.throw(
			_("Medical leave can only be decided by HR or a named backup approver for this employee."),
			frappe.PermissionError,
		)


def check_canceller(doc, method=None) -> None:
	"""Q32: only HR who can see the employee may cancel medical leave, because cancelling gives
	the days back."""
	settings = _settings()
	if not _is_medical(doc, settings):
		return
	user = frappe.session.user
	if user == "Administrator":
		return
	if not _is_hr(user) or not _can_see_application(user, doc):
		frappe.throw(_("Only HR can cancel medical leave."), frappe.PermissionError)


def notify_hr_of_backup_decision(doc, method=None) -> None:
	"""Q23: whenever a backup decides medical leave, the HR users who can see the employee are told."""
	settings = _settings()
	if not _is_medical(doc, settings):
		return
	user = frappe.session.user
	if _is_hr(user) or user not in _backups(settings):
		return
	recipients = sorted(
		{
			hr_user
			for role in HR_ROLES
			for hr_user in queries.get_enabled_users_with_role(role)
			if hr_user != user and _can_see_application(hr_user, doc)
		}
	)
	if not recipients:
		return
	details = _("{0} ({1}), {2} to {3}: {4} by backup approver {5}.").format(
		doc.employee_name,
		doc.employee,
		formatdate(doc.from_date),
		formatdate(doc.to_date),
		_(doc.status),
		user,
	)
	frappe.sendmail(
		recipients=recipients,
		subject=_("Medical leave {0} by backup approver").format(_(doc.status).lower()),
		message=f"<p>{escape_html(details)}</p>",
		reference_doctype=doc.doctype,
		reference_name=doc.name,
	)
