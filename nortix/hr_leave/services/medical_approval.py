"""Medical leave approval by HR and named backups (LV-007, LV-009, Q23)."""

import frappe
from frappe import _
from frappe.utils import escape_html, formatdate, get_fullname

from nortix.hr_leave.services import queries

HR_ROLES = ("HR Manager", "HR User")
DECISIONS = ("Approved", "Rejected")


def _settings():
	return frappe.get_cached_doc("Nortix Leave Settings")


def _is_medical(doc, settings) -> bool:
	return bool(settings.medical_leave_type) and doc.leave_type == settings.medical_leave_type


def _backups(settings) -> set[str]:
	return {row.user for row in settings.medical_backup_approvers or []}


def _is_hr(user: str) -> bool:
	return bool(set(frappe.get_roles(user)) & set(HR_ROLES))


def validate_medical_settings(settings) -> None:
	"""Q23: the named approver must be HR; backups must be active users who can decide leave."""
	if settings.medical_leave_approver and not _is_hr(settings.medical_leave_approver):
		frappe.throw(
			_("The Medical Leave Approver {0} must have the HR Manager or HR User role.").format(
				frappe.bold(settings.medical_leave_approver)
			),
			title=_("Approver Not HR"),
		)
	for row in settings.medical_backup_approvers or []:
		enabled, user_type = frappe.db.get_value("User", row.user, ["enabled", "user_type"]) or (0, None)
		if not enabled or user_type != "System User":
			frappe.throw(
				_("Backup approver {0} must be an enabled system user.").format(frappe.bold(row.user)),
				title=_("Backup Approver Not Allowed"),
			)
		# Frappe HR lets only Leave Approver and HR roles change an application's status.
		if not set(frappe.get_roles(row.user)) & {"Leave Approver", *HR_ROLES}:
			frappe.throw(
				_("Backup approver {0} needs the Leave Approver role to approve or reject leave.").format(
					frappe.bold(row.user)
				),
				title=_("Backup Approver Not Allowed"),
			)


def route_to_hr(doc, method=None) -> None:
	"""LV-007: a draft medical application goes to the named HR user, not the reporting manager."""
	settings = _settings()
	if doc.docstatus or not _is_medical(doc, settings) or not settings.medical_leave_approver:
		return
	if doc.leave_approver != settings.medical_leave_approver:
		doc.leave_approver = settings.medical_leave_approver
		doc.leave_approver_name = get_fullname(settings.medical_leave_approver)


def share_with_backups(doc, method=None) -> None:
	"""Backups need not hold an HR role, so each medical application is shared with them so they
	can open and decide it."""
	settings = _settings()
	if doc.docstatus or not _is_medical(doc, settings):
		return
	for user in _backups(settings):
		frappe.share.add_docshare(
			doc.doctype, doc.name, user, write=1, submit=1, flags={"ignore_share_permission": True}
		)


def remove_shares_of_removed_backups(settings) -> None:
	"""A user taken off the backup list loses access to open medical applications at once."""
	before = settings.get_doc_before_save()
	if not before:
		return
	removed = _backups(before) - _backups(settings)
	if not removed or not settings.medical_leave_type:
		return
	open_applications = frappe.get_all(
		"Leave Application",
		filters={"leave_type": settings.medical_leave_type, "docstatus": 0},
		pluck="name",
	)
	for name in open_applications:
		for user in removed:
			frappe.share.remove("Leave Application", name, user, flags={"ignore_share_permission": True})


def check_approver(doc, method=None) -> None:
	"""LV-007, LV-009: only HR or a named backup may decide medical leave, and never their own.
	Applies to the form and the API alike, because both submit the document."""
	settings = _settings()
	if not _is_medical(doc, settings) or doc.status not in DECISIONS:
		return
	user = frappe.session.user
	if user == "Administrator":
		return
	if user == frappe.db.get_value("Employee", doc.employee, "user_id"):
		frappe.throw(_("You cannot decide your own medical leave."), frappe.PermissionError)
	if _is_hr(user) or user in _backups(settings):
		return
	frappe.throw(
		_("Medical leave can only be decided by HR or a named backup approver."), frappe.PermissionError
	)


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
			if hr_user != user and frappe.has_permission("Employee", "read", doc.employee, user=hr_user)
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
