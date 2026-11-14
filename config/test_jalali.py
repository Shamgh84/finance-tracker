from datetime import date, timedelta

from django.test import SimpleTestCase

from .jalali import (
    from_jalali,
    jalali_month_range,
    month_label,
    shift_month,
    to_jalali,
)


class JalaliTests(SimpleTestCase):
    def test_to_jalali_known_date(self):
        self.assertEqual(to_jalali(date(2026, 11, 13)), (1405, 8, 22))

    def test_nowruz_1405(self):
        self.assertEqual(from_jalali(1405, 1, 1), date(2026, 3, 21))

    def test_month_lengths(self):
        def length(year, month):
            start, end = jalali_month_range(year, month)
            return (end - start).days + 1

        self.assertEqual(length(1405, 1), 31)
        self.assertEqual(length(1405, 7), 30)
        self.assertEqual(length(1403, 12), 30)   # سال کبیسه
        self.assertEqual(length(1404, 12), 29)

    def test_months_are_contiguous(self):
        for month in range(1, 13):
            _, end = jalali_month_range(1405, month)
            next_year, next_month = (1405, month + 1) if month < 12 else (1406, 1)
            next_start, _ = jalali_month_range(next_year, next_month)
            self.assertEqual(end + timedelta(days=1), next_start)

    def test_roundtrip(self):
        day = date(2026, 1, 1)
        for _ in range(400):
            self.assertEqual(from_jalali(*to_jalali(day)), day)
            day += timedelta(days=1)

    def test_shift_month(self):
        self.assertEqual(shift_month(1405, 1, -1), (1404, 12))
        self.assertEqual(shift_month(1404, 12, 1), (1405, 1))
        self.assertEqual(shift_month(1405, 8, -2), (1405, 6))

    def test_month_label(self):
        self.assertEqual(month_label(1405, 8), 'آبان 1405')