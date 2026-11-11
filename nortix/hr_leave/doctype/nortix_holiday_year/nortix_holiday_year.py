import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, getdate

from nortix.hr_leave.services.calendar import build_calendar


class NortixHolidayYear(Document):
	def validate(self):
		seen = set()
		for row in self.holidays:
			holiday_date = getdate(row.holiday_date)
			if holiday_date.year != cint(self.year):
				frappe.throw(_("Row {0}: {1} is not in {2}.").format(row.idx, row.holiday_date, self.year))
			if holiday_date in seen:
				frappe.throw(_("Row {0}: {1} is entered twice.").format(row.idx, row.holiday_date))
			seen.add(holiday_date)

	def on_update(self):
		build_calendar(self.year)
