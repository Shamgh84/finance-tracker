from datetime import date
from decimal import Decimal

from django.test import SimpleTestCase
from rest_framework.test import APITestCase

from accounts.models import User
from budgets.models import Budget
from categories.models import Category
from transactions.models import Transaction
from . import services


class PureFunctionTests(SimpleTestCase):
    def test_calc_change_up(self):
        result = services.calc_change(300, 100)
        self.assertEqual(result['trend'], 'up')
        self.assertEqual(result['change'], Decimal('200'))
        self.assertEqual(result['change_percent'], Decimal('200.0'))

    def test_calc_change_down(self):
        result = services.calc_change(50, 100)
        self.assertEqual(result['trend'], 'down')
        self.assertEqual(result['change_percent'], Decimal('-50.0'))

    def test_calc_change_new_category(self):
        result = services.calc_change(100, 0)
        self.assertEqual(result['trend'], 'new')
        self.assertIsNone(result['change_percent'])

    def test_calc_change_both_zero(self):
        self.assertEqual(services.calc_change(0, 0)['trend'], 'same')

    def test_project_month_end(self):
        self.assertEqual(
            services.project_month_end(1500, 15, 30), Decimal('3000.00')
        )

    def test_health_score_good(self):
        result = services.calculate_health_score(1000, 800, 800, 800, 0, 0)
        self.assertEqual(result['score'], 85)
        self.assertEqual(result['level'], 'excellent')

    def test_health_score_bad(self):
        result = services.calculate_health_score(1000, 1200, 2000, 800, 2, 2)
        self.assertEqual(result['score'], 0)
        self.assertEqual(result['level'], 'poor')

    def test_health_score_without_income(self):
        result = services.calculate_health_score(0, 500, 500, 500, 0, 0)
        self.assertEqual(result['score'], 35)
        self.assertIsNone(result['savings_rate_percent'])

    def test_build_insights_mentions_category_and_score(self):
        comparison = {
            'change_percent': Decimal('50.0'),
            'trend': 'up',
            'previous_expense': Decimal('100'),
            'categories': [{
                'category_name': 'خوراک', 'trend': 'up',
                'change_percent': Decimal('200.0'), 'change': Decimal('200'),
            }],
        }
        forecast = {
            'spent_so_far': Decimal('0'),
            'previous_month_expense': Decimal('0'),
            'projected_expense': Decimal('0'),
        }
        health = {
            'income': Decimal('1000'), 'expense': Decimal('500'),
            'savings_rate_percent': Decimal('50.0'),
            'budgets': {'count': 0, 'exceeded': 0},
            'score': 85, 'level_label': 'عالی',
        }
        insights = services.build_insights(comparison, forecast, health)
        self.assertTrue(any('خوراک' in text for text in insights))
        self.assertTrue(any('85' in text for text in insights))


class AnalysisTests(APITestCase):
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
        self.client.force_authenticate(self.u1)

    def add(self, user, category, amount, day):
        return Transaction.objects.create(
            user=user, category=category, amount=amount, date=day
        )

    def test_comparison_current_month_uses_same_day_cap(self):
        today = date(2026, 6, 15)
        self.add(self.u1, self.food, 300, date(2026, 6, 5))
        self.add(self.u1, self.other, 50, date(2026, 6, 10))
        self.add(self.u1, self.food, 100, date(2026, 5, 10))
        self.add(self.u1, self.food, 400, date(2026, 5, 20))   # بعد از روز ۱۵، حساب نمی‌شود
        self.add(self.u2, self.food, 999, date(2026, 6, 5))    # کاربر دیگر

        result = services.get_month_comparison(self.u1, 2026, 6, today)
        self.assertEqual(result['compared_through_day'], 15)
        self.assertEqual(result['current_expense'], Decimal('350'))
        self.assertEqual(result['previous_expense'], Decimal('100'))
        self.assertEqual(result['trend'], 'up')

        by_name = {c['category_name']: c for c in result['categories']}
        self.assertEqual(by_name['خوراک']['change_percent'], Decimal('200.0'))
        self.assertEqual(by_name[self.other.name]['trend'], 'new')

    def test_comparison_completed_month_has_no_cap(self):
        today = date(2026, 6, 15)
        self.add(self.u1, self.food, 100, date(2026, 4, 10))
        self.add(self.u1, self.food, 400, date(2026, 5, 20))

        result = services.get_month_comparison(self.u1, 2026, 5, today)
        self.assertIsNone(result['compared_through_day'])
        self.assertEqual(result['current_expense'], Decimal('400'))
        self.assertEqual(result['previous_expense'], Decimal('100'))

    def test_forecast(self):
        today = date(2026, 6, 15)
        self.add(self.u1, self.food, 1500, date(2026, 6, 3))
        self.add(self.u1, self.salary, 9999, date(2026, 6, 2))   # درآمد است
        self.add(self.u1, self.food, 777, date(2026, 6, 20))     # آینده است
        self.add(self.u1, self.food, 2000, date(2026, 5, 10))

        result = services.get_forecast(self.u1, today)
        self.assertEqual(result['spent_so_far'], Decimal('1500'))
        self.assertEqual(result['daily_average'], Decimal('100.00'))
        self.assertEqual(result['projected_expense'], Decimal('3000.00'))
        self.assertEqual(result['previous_month_expense'], Decimal('2000'))
        self.assertEqual(result['days_in_month'], 30)

    def test_health_score_counts_exceeded_budgets(self):
        today = date(2026, 6, 15)
        Budget.objects.create(
            user=self.u1, category=self.food, year=2026, month=6, limit_amount=1000
        )
        self.add(self.u1, self.salary, 5000, date(2026, 6, 2))
        self.add(self.u1, self.food, 1200, date(2026, 6, 3))

        result = services.get_health_score(self.u1, today)
        self.assertEqual(result['budgets'], {'count': 1, 'exceeded': 1})
        self.assertEqual(result['score'], 60)
        self.assertEqual(result['level'], 'good')

    def test_comparison_endpoint_default(self):
        res = self.client.get('/api/analytics/comparison/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('categories', res.data)

    def test_comparison_requires_year_and_month_together(self):
        res = self.client.get('/api/analytics/comparison/?year=2026')
        self.assertEqual(res.status_code, 400)

    def test_comparison_explicit_month(self):
        res = self.client.get('/api/analytics/comparison/?year=2026&month=5')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['month'], '2026-05')

    def test_forecast_endpoint(self):
        res = self.client.get('/api/analytics/forecast/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('projected_expense', res.data)

    def test_health_score_endpoint(self):
        res = self.client.get('/api/analytics/health-score/')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(0 <= res.data['score'] <= 100)

    def test_report_endpoint(self):
        res = self.client.get('/api/analytics/report/')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(res.data['insights']) >= 1)

    def test_report_requires_authentication(self):
        self.client.force_authenticate(None)
        res = self.client.get('/api/analytics/report/')
        self.assertIn(res.status_code, (401, 403))