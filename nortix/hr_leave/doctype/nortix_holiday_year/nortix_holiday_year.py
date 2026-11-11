import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, getdate, today

from nortix.hr_leave.services.calendar import build_calendar

FIRST_YEAR = 2000


class NortixHolidayYear(Document):
	def validate(self):
		self.validate_editor()
		self.validate_year()
		self.validate_holidays()

	def validate_editor(self):
		"""LV-014: the calendar sets how leave is counted in every company, so only group-wide
		HR (no company restriction) may change it. The daily job creates empty years itself."""
		if self.flags.from_daily_job or frappe.session.user == "Administrator":
			return
		if frappe.permissions.get_user_permissions(frappe.session.user).get("Company"):
			frappe.throw(
				_(
					"Only HR users who are not limited to a company can change the holiday calendar, because it applies to every company."
				),
				frappe.PermissionError,
			)

	def validate_year(self):
		latest = getdate(today()).year + 1
		if not FIRST_YEAR <= cint(self.year) <= latest:
			frappe.throw(_("Year must be between {0} and {1}.").format(FIRST_YEAR, latest))

	def validate_holidays(self):
		seen = set()
		for row in self.holidays:
			holiday_date = getdate(row.holiday_date)
			if holiday_date.year != cint(self.year):
				frappe.throw(_("Row {0}: {1} is not in {2}.").format(row.idx, row.holiday_date, self.year))
			if holiday_date in seen:
				frappe.throw(_("Row {0}: {1} is entered twice.").format(row.idx, row.holiday_date))
			seen.add(holiday_date)

	def on_update(self):
		build_calendar(self.year, log_conflicts=not self.flags.from_daily_job)
