from frappe.model.document import Document

from nortix.hr_leave.services.annual import validate_annual_settings


class NortixLeaveSettings(Document):
	def validate(self):
		validate_annual_settings(self)
