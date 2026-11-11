from datetime import date

import frappe
from frappe.tests import UnitTestCase

from nortix.hr_leave.services.leave_rules import (
	get_additional_entitlement,
	get_casual_entitlement,
	get_medical_entitlement,
)

PERIOD_FROM = "2026-01-01"
PERIOD_TO = "2026-12-31"


def settings(**values):
	base = {
		"casual_monthly_days_first_year": 0.5,
		"casual_days_before_mark": 6,
		"casual_days_after_mark": 7,
		"additional_days_before_mark": 1,
		"medical_days": 7,
	}
	base.update(values)
	return frappe._dict(base)


def as_tuple(entitlement):
	return entitlement and (str(entitlement.from_date), str(entitlement.to_date), entitlement.days)


class TestCasualEntitlement(UnitTestCase):
	"""LV-003, LV-004: casual leave by month in the joining year, 6 before the mark, 7 from it."""

	def casual(self, join_date, on_date, **values):
		return as_tuple(
			get_casual_entitlement(join_date, PERIOD_FROM, PERIOD_TO, on_date, settings(**values))
		)

	def test_joining_year_counts_join_month_in_full(self):
		cases = {
			"2026-01-01": 6.0,
			"2026-05-10": 4.0,
			"2026-05-31": 4.0,
			"2026-12-01": 0.5,
		}
		for join_date, days in cases.items():
			with self.subTest(join_date=join_date):
				self.assertEqual(self.casual(join_date, join_date), (join_date, PERIOD_TO, days))

	def test_nothing_before_joining(self):
		self.assertIsNone(self.casual("2026-05-10", "2026-05-09"))

	def test_later_year_before_mark_gives_6(self):
		self.assertEqual(self.casual("2025-11-01", "2026-10-31"), (PERIOD_FROM, PERIOD_TO, 6))

	def test_mark_date_gives_7(self):
		self.assertEqual(self.casual("2025-11-01", "2026-11-01"), (PERIOD_FROM, PERIOD_TO, 7))

	def test_mark_before_period_gives_7(self):
		self.assertEqual(self.casual("2024-08-10", "2026-01-01"), (PERIOD_FROM, PERIOD_TO, 7))

	def test_amounts_come_from_settings(self):
		self.assertEqual(self.casual("2026-07-01", "2026-07-01", casual_monthly_days_first_year=1)[2], 6)
		self.assertEqual(self.casual("2025-11-01", "2026-03-01", casual_days_before_mark=5)[2], 5)

	def test_zero_amount_gives_nothing(self):
		self.assertIsNone(self.casual("2025-11-01", "2026-03-01", casual_days_before_mark=0))

	def test_29_feb_joiner_rises_on_28_feb(self):
		def casual_2025(on_date):
			return as_tuple(
				get_casual_entitlement("2024-02-29", "2025-01-01", "2025-12-31", on_date, settings())
			)

		self.assertEqual(casual_2025("2025-02-27")[2], 6)
		self.assertEqual(casual_2025("2025-02-28")[2], 7)

	def test_mark_on_period_start_gives_7(self):
		self.assertEqual(
			as_tuple(
				get_casual_entitlement("2026-01-01", "2027-01-01", "2027-12-31", "2027-01-01", settings())
			),
			("2027-01-01", "2027-12-31", 7),
		)

	def test_31_dec_joiner_gets_half_day(self):
		self.assertEqual(self.casual("2026-12-31", "2026-12-31"), ("2026-12-31", PERIOD_TO, 0.5))


class TestAdditionalEntitlement(UnitTestCase):
	"""LV-005: 1 day per period before the mark, usable until the day before the mark."""

	def additional(self, join_date, on_date, period_from=PERIOD_FROM, period_to=PERIOD_TO):
		return as_tuple(get_additional_entitlement(join_date, period_from, period_to, on_date, settings()))

	def test_joining_year_from_join_date(self):
		self.assertEqual(self.additional("2026-05-10", "2026-05-10"), ("2026-05-10", PERIOD_TO, 1))

	def test_mark_year_ends_day_before_mark(self):
		self.assertEqual(self.additional("2025-11-01", "2026-01-01"), (PERIOD_FROM, "2026-10-31", 1))

	def test_nothing_from_mark_date(self):
		self.assertIsNone(self.additional("2025-11-01", "2026-11-01"))

	def test_nothing_when_mark_is_period_start(self):
		self.assertIsNone(self.additional("2025-01-01", "2026-01-01"))

	def test_nothing_after_mark_year(self):
		self.assertIsNone(self.additional("2024-08-10", "2026-01-01"))

	def test_1_jan_joiner_has_whole_year(self):
		self.assertEqual(self.additional("2026-01-01", "2026-01-01"), (PERIOD_FROM, PERIOD_TO, 1))

	def test_31_dec_joiner_has_one_day_then_until_day_before_mark(self):
		self.assertEqual(
			self.additional("2025-12-31", "2025-12-31", "2025-01-01", "2025-12-31"),
			("2025-12-31", "2025-12-31", 1),
		)
		self.assertEqual(self.additional("2025-12-31", "2026-01-01"), (PERIOD_FROM, "2026-12-30", 1))

	def test_29_feb_joiner_ends_27_feb(self):
		self.assertEqual(
			self.additional("2024-02-29", "2025-01-01", "2025-01-01", "2025-12-31"),
			("2025-01-01", "2025-02-27", 1),
		)


class TestMedicalEntitlement(UnitTestCase):
	"""LV-007: 7 days per period from joining, in full in the joining year (Q20)."""

	def medical(self, join_date, on_date):
		return as_tuple(get_medical_entitlement(join_date, PERIOD_FROM, PERIOD_TO, on_date, settings()))

	def test_joining_year_full_amount_from_join_date(self):
		self.assertEqual(self.medical("2026-05-10", "2026-05-10"), ("2026-05-10", PERIOD_TO, 7))
		self.assertEqual(self.medical("2026-12-30", "2026-12-30"), ("2026-12-30", PERIOD_TO, 7))

	def test_later_year_from_period_start(self):
		self.assertEqual(self.medical("2025-03-01", "2026-01-01"), (PERIOD_FROM, PERIOD_TO, 7))

	def test_nothing_before_joining(self):
		self.assertIsNone(self.medical("2026-05-10", "2026-05-09"))

	def test_entitlement_dates_are_dates(self):
		entitlement = get_medical_entitlement("2026-05-10", PERIOD_FROM, PERIOD_TO, "2026-06-01", settings())
		self.assertEqual(entitlement.from_date, date(2026, 5, 10))
