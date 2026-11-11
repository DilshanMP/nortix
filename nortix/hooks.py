app_name = "nortix"
app_title = "Nortix"
app_publisher = "Pasindu Dilshan"
app_description = "Department-organised multi-company business platform on Frappe HR and ERPNext"
app_email = "mpdilshan.99@gmail.com"
app_license = "Proprietary"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "nortix",
# 		"logo": "/assets/nortix/logo.png",
# 		"title": "Nortix",
# 		"route": "/nortix",
# 		"has_permission": "nortix.api.permission.has_app_permission",
# 	}
# ]

# The dock, the rail down the left of the desk, is a document rather than a hook. Author it in
# Manage Dock on a developer-mode site and press Export to App, and it is written to
# `nortix/dock/nortix/nortix.json` for git to carry. An app that ships none has no
# rail: its sidebar gets a switcher in the header instead.
#
# A companion app, one that extends a host app rather than standing on its own, says so with
# `mount_on` on that same record, and its entries are appended to the host's rail. Mounting keeps
# the companion off the apps screen, so it takes precedence over any add_to_apps_screen above.

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/nortix/css/nortix.css"
# app_include_js = "/assets/nortix/js/nortix.js"

# include js, css files in header of web template
# web_include_css = "/assets/nortix/css/nortix.css"
# web_include_js = "/assets/nortix/js/nortix.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "nortix/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_kanban_js = {"doctype" : "public/js/doctype_kanban.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "nortix/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "nortix.utils.jinja_methods",
# 	"filters": "nortix.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "nortix.install.before_install"
after_install = "nortix.hr_leave.setup.after_install"

# Uninstallation
# ------------

# before_uninstall = "nortix.uninstall.before_uninstall"
# after_uninstall = "nortix.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "nortix.utils.before_app_install"
# after_app_install = "nortix.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "nortix.utils.before_app_uninstall"
# after_app_uninstall = "nortix.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "nortix.build.after_build"

# To hook into the build process of other apps
# The list of apps being built is passed as an argument

# after_app_build = "nortix.build.after_app_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "nortix.notifications.get_notification_config"

# Awesome Bar
# -----------
# Extra search results: list of dicts with label, description, route, index.
# route: ["List", "ToDo"], "/desk/docs/some/page", or "https://example.com"
# awesomebar_search = ["nortix.search.awesomebar_results"]

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Leave Allocation": {
		"validate": "nortix.hr_leave.services.allocation_source.validate_allocation_source",
	},
	"Leave Adjustment": {
		"validate": "nortix.hr_leave.services.allocation_source.validate_allocation_source",
	},
	"Leave Application": {
		"validate": "nortix.hr_leave.services.medical_approval.route_to_hr",
		"on_update": "nortix.hr_leave.services.medical_approval.share_with_backups",
		"before_submit": "nortix.hr_leave.services.medical_approval.check_approver",
		"on_submit": "nortix.hr_leave.services.medical_approval.notify_hr_of_backup_decision",
	},
}

# Saturday half days must count 0.5 leave day (LV-014); no other installed app overrides this class.
override_doctype_class = {
	"Leave Application": "nortix.hr_leave.overrides.NortixLeaveApplication",
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily": [
		"nortix.hr_leave.tasks.daily",
	],
	"weekly": [
		"nortix.hr_leave.tasks.weekly",
	],
}

# Testing
# -------

# before_tests = "nortix.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "nortix.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
	"hrms.hr.doctype.leave_application.leave_application.get_number_of_leave_days": "nortix.hr_leave.overrides.get_number_of_leave_days",
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "nortix.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["nortix.utils.before_request"]
# after_request = ["nortix.utils.after_request"]

# Job Events
# ----------
# before_job = ["nortix.utils.before_job"]
# after_job = ["nortix.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"nortix.auth.validate"
# ]

# on_social_login = "nortix.auth.on_social_login"

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []
