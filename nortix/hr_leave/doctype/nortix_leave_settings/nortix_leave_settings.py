from frappe.model.document import Document

from nortix.hr_leave.services.annual import validate_annual_settings
from nortix.hr_leave.services.balance_alerts import validate_alert_settings
from nortix.hr_leave.services.leave_allocation_job import validate_leave_settings
from nortix.hr_leave.services.medical_approval import validate_medical_settings


class NortixLeaveSettings(Document):
	def validate(self):
		validate_annual_settings(self)
		validate_leave_settings(self)
		validate_alert_settings(self)
		validate_medical_settings(self)
