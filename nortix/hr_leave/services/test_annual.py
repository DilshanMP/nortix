from datetime import date

import frappe
from frappe.tests import UnitTestCase

from nortix.hr_leave.services.annual import get_annual_entitlement, get_mark_date

PERIOD_FROM = "2026-01-01"
PERIOD_TO = "2026-12-31"


def settings(**values):
	base = {
		"annual_q1_days": 14,
		"annual_q2_days": 10,
		"annual_q3_days": 7,
		"annual_q4_days": 4,
		"annual_full_days": 14,
	}
	base.update(values)
	return frappe._dict(base)


def entitlement(join_date, on_date=PERIOD_TO, **setting_values):
	return get_annual_entitlement(join_date, PERIOD_FROM, PERIOD_TO, on_date, settings(**setting_values))


class TestMarkDate(UnitTestCase):
	"""LV-006, Q9, Q10: the 1-year mark is the anniversary of the join date."""

	def test_mark_is_join_plus_12_months(self):
		self.assertEqual(get_mark_date("2025-11-01"), date(2026, 11, 1))

	def test_mark_for_29_feb_join_is_28_feb(self):
		self.assertEqual(get_mark_date("2024-02-29"), date(2025, 2, 28))


class TestAnnualEntitlement(UnitTestCase):
	"""LV-006: amount by the quarter of the mark in the mark's period, full amount later."""

	def test_quarter_boundaries(self):
		cases = {
			"2025-01-01": 14,
			"2025-03-31": 14,
			"2025-04-01": 10,
			"2025-06-30": 10,
			"2025-07-01": 7,
			"2025-09-30": 7,
			"2025-10-01": 4,
			"2025-12-31": 4,
		}
		for join_date, days in cases.items():
			with self.subTest(join_date=join_date):
				self.assertEqual(entitlement(join_date).days, days)

	def test_joined_1_apr_2025_gets_10_in_2026(self):
		result = entitlement("2025-04-01")
		self.assertEqual((result.from_date, result.days), (date(2026, 4, 1), 10))

	def test_mark_1_nov_gives_4_from_mark_date(self):
		result = entitlement("2025-11-01", on_date="2026-11-01")
		self.assertEqual((result.from_date, result.days), (date(2026, 11, 1), 4))

	def test_nothing_on_day_before_mark(self):
		self.assertIsNone(entitlement("2025-11-01", on_date="2026-10-31"))

	def test_mark_year_starts_on_mark_date(self):
		self.assertEqual(entitlement("2025-02-15").from_date, date(2026, 2, 15))

	def test_29_feb_join_counts_in_q1(self):
		result = get_annual_entitlement("2024-02-29", "2025-01-01", "2025-12-31", "2025-02-28", settings())
		self.assertEqual((result.from_date, result.days), (date(2025, 2, 28), 14))

	def test_29_feb_joiner_has_nothing_on_27_feb(self):
		self.assertIsNone(
			get_annual_entitlement("2024-02-29", "2025-01-01", "2025-12-31", "2025-02-27", settings())
		)

	def test_later_period_gets_full_days_from_period_start(self):
		result = entitlement("2024-11-01", on_date="2026-01-01")
		self.assertEqual((result.from_date, result.days), (date(2026, 1, 1), 14))

	def test_mark_after_period_gives_nothing(self):
		self.assertIsNone(entitlement("2026-03-01"))

	def test_amounts_come_from_settings(self):
		self.assertEqual(entitlement("2025-10-15", annual_q4_days=5).days, 5)
		self.assertEqual(entitlement("2024-05-01", annual_full_days=16).days, 16)

	def test_zero_amount_gives_nothing(self):
		self.assertIsNone(entitlement("2025-10-15", annual_q4_days=0))
