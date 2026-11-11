from datetime import date

from frappe.tests import UnitTestCase

from nortix.hr_leave.services.calendar import get_calendar_rows, get_saturday_correction

SATURDAYS_MARCH = ["2026-03-07", "2026-03-14", "2026-03-21", "2026-03-28"]


def hrms_days(from_date, to_date, holidays, half_day=False, half_day_date=None):
	"""What Frappe HR counts before the correction: calendar days, minus 0.5 for a half-day
	request, minus every holiday in the range as a whole day."""
	start, end = date.fromisoformat(from_date), date.fromisoformat(to_date)
	days = (end - start).days + 1
	if half_day:
		days -= 0.5
	return days - sum(1 for holiday in holidays if from_date <= holiday <= to_date)


def counted(from_date, to_date, holidays, half_days=SATURDAYS_MARCH, half_day=False, half_day_date=None):
	return hrms_days(from_date, to_date, holidays, half_day, half_day_date) + get_saturday_correction(
		from_date, to_date, half_day, half_day_date, [date.fromisoformat(d) for d in half_days]
	)


MARCH_HOLIDAYS = [*SATURDAYS_MARCH, "2026-03-01", "2026-03-08", "2026-03-15", "2026-03-22", "2026-03-29"]


class TestSaturdayCorrection(UnitTestCase):
	"""LV-014, Q28: a Saturday counts 0.5 leave day; Sundays and mercantile holidays count 0."""

	def test_acceptance_table(self):
		cases = {
			("2026-03-06", "2026-03-07"): 1.5,
			("2026-03-07", "2026-03-09"): 1.5,
			("2026-03-02", "2026-03-06"): 5,
			("2026-03-02", "2026-03-08"): 5.5,
		}
		for (from_date, to_date), days in cases.items():
			with self.subTest(from_date=from_date, to_date=to_date):
				self.assertEqual(counted(from_date, to_date, MARCH_HOLIDAYS), days)

	def test_mercantile_holiday_counts_zero(self):
		holidays = [*MARCH_HOLIDAYS, "2026-03-03"]
		self.assertEqual(counted("2026-03-03", "2026-03-03", holidays), 0)

	def test_half_day_request_on_saturday_counts_half(self):
		self.assertEqual(counted("2026-03-07", "2026-03-07", MARCH_HOLIDAYS, half_day=True), 0.5)
		self.assertEqual(
			counted("2026-03-06", "2026-03-07", MARCH_HOLIDAYS, half_day=True, half_day_date="2026-03-07"),
			1.5,
		)

	def test_half_day_request_on_weekday_unchanged(self):
		self.assertEqual(
			counted("2026-03-06", "2026-03-07", MARCH_HOLIDAYS, half_day=True, half_day_date="2026-03-06"), 1
		)

	def test_no_saturday_no_correction(self):
		self.assertEqual(get_saturday_correction("2026-03-02", "2026-03-06", False, None, []), 0)


class TestCalendarRows(UnitTestCase):
	"""LV-014: every Sunday off, every Saturday a half day, mercantile holidays full days."""

	def rows(self, holidays=None):
		return {row["holiday_date"]: row for row in get_calendar_rows(2026, holidays or [])}

	def test_every_sunday_and_saturday(self):
		rows = self.rows()
		sundays = [d for d, r in rows.items() if d.weekday() == 6]
		saturdays = [d for d, r in rows.items() if d.weekday() == 5]
		self.assertEqual((len(sundays), len(saturdays)), (52, 52))
		self.assertTrue(all(rows[d]["weekly_off"] and not rows[d]["is_half_day"] for d in sundays))
		self.assertTrue(all(rows[d]["weekly_off"] and rows[d]["is_half_day"] for d in saturdays))
		self.assertEqual(len(rows), 104)

	def test_mercantile_holiday_on_weekday_is_full_day(self):
		rows = self.rows([{"holiday_date": "2026-03-03", "description": "Test Holiday"}])
		row = rows[date(2026, 3, 3)]
		self.assertEqual((row["weekly_off"], row["is_half_day"], row["description"]), (0, 0, "Test Holiday"))

	def test_mercantile_holiday_on_saturday_becomes_full_day(self):
		rows = self.rows([{"holiday_date": "2026-03-07", "description": "Test Holiday"}])
		row = rows[date(2026, 3, 7)]
		self.assertEqual((row["is_half_day"], row["description"]), (0, "Test Holiday"))
		self.assertEqual(len(rows), 104)

	def test_mercantile_holiday_on_sunday_is_not_duplicated(self):
		rows = self.rows([{"holiday_date": "2026-03-08", "description": "Test Holiday"}])
		self.assertEqual(len(rows), 104)
		self.assertEqual(rows[date(2026, 3, 8)]["description"], "Test Holiday")

	def test_holiday_outside_year_is_ignored(self):
		self.assertEqual(len(self.rows([{"holiday_date": "2027-01-01", "description": "Next Year"}])), 104)
