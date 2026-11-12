from datetime import date, timedelta
from decimal import Decimal

from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import User
from categories.models import Category
from transactions.models import Transaction
from .services import shift_month


def D(value):
    return Decimal(str(value))


class DashboardAPITests(APITestCase):
    def setUp(self):
        self.u1 = User.objects.create_user(
            username='u1', email='u1@example.com', password='Pass12345!x'
        )
        self.u2 = User.objects.create_user(
            username='u2', email='u2@example.com', password='Pass12345!x'
        )
        self.food = Category.objects.get(user=None, name='خوراک', type='expense')
        self.other = Category.objects.filter(
            user=None, type='expense'
        ).exclude(pk=self.food.pk).first()
        self.salary = Category.objects.get(user=None, name='حقوق', type='income')
        self.today = timezone.localdate()
        self.client.force_authenticate(self.u1)

    def add(self, user, category, amount, day):
        return Transaction.objects.create(
            user=user, category=category, amount=amount, date=day
        )

    def test_summary_defaults_to_current_month(self):
        self.add(self.u1, self.salary, 5000, self.today)
        self.add(self.u1, self.food, 1200, self.today)
        last_month = self.today.replace(day=1) - timedelta(days=1)
        self.add(self.u1, self.food, 800, last_month)

        res = self.client.get('/api/analytics/summary/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(D(res.data['period_income']), D(5000))
        self.assertEqual(D(res.data['period_expense']), D(1200))
        self.assertEqual(D(res.data['period_net']), D(3800))
        self.assertEqual(D(res.data['total_income']), D(5000))
        self.assertEqual(D(res.data['total_expense']), D(2000))
        self.assertEqual(D(res.data['balance']), D(3000))

    def test_summary_ignores_other_users(self):
        self.add(self.u1, self.food, 100, self.today)
        self.add(self.u2, self.salary, 9999, self.today)
        res = self.client.get('/api/analytics/summary/')
        self.assertEqual(D(res.data['total_income']), D(0))
        self.assertEqual(D(res.data['total_expense']), D(100))

    def test_summary_custom_range(self):
        self.add(self.u1, self.food, 100, date(2026, 1, 10))
        self.add(self.u1, self.food, 200, date(2026, 2, 10))
        res = self.client.get(
            '/api/analytics/summary/?date_from=2026-01-01&date_to=2026-01-31'
        )
        self.assertEqual(D(res.data['period_expense']), D(100))
        self.assertEqual(D(res.data['total_expense']), D(300))

    def test_invalid_date_range_rejected(self):
        res = self.client.get(
            '/api/analytics/summary/?date_from=2026-02-01&date_to=2026-01-01'
        )
        self.assertEqual(res.status_code, 400)

    def test_category_breakdown_percentages(self):
        self.add(self.u1, self.food, 300, self.today)
        self.add(self.u1, self.other, 100, self.today)
        self.add(self.u1, self.salary, 9999, self.today)  # درآمد است و نباید بیاید

        res = self.client.get('/api/analytics/by-category/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(D(res.data['total']), D(400))
        self.assertEqual(len(res.data['categories']), 2)
        first = res.data['categories'][0]
        self.assertEqual(first['category_name'], 'خوراک')
        self.assertEqual(D(first['percent']), D('75.0'))

    def test_trend_fills_missing_months(self):
        year, month = shift_month(self.today.year, self.today.month, -2)
        self.add(self.u1, self.food, 500, date(year, month, 15))
        self.add(self.u1, self.food, 200, self.today)

        res = self.client.get('/api/analytics/trend/?months=3')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 3)
        self.assertEqual(D(res.data[0]['expense']), D(500))
        self.assertEqual(D(res.data[1]['expense']), D(0))
        self.assertEqual(D(res.data[2]['expense']), D(200))
        self.assertEqual(res.data[2]['month'], self.today.strftime('%Y-%m'))

    def test_trend_months_limit(self):
        res = self.client.get('/api/analytics/trend/?months=100')
        self.assertEqual(res.status_code, 400)

    def test_requires_authentication(self):
        self.client.force_authenticate(None)
        res = self.client.get('/api/analytics/summary/')
        self.assertIn(res.status_code, (401, 403))