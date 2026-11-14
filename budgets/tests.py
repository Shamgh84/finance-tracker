from datetime import timedelta
from decimal import Decimal

from django.test import SimpleTestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import User
from categories.models import Category
from config.jalali import current_jalali_month, jalali_month_range
from transactions.models import Transaction
from .models import Budget
from .services import calculate_status


class CalculateStatusTests(SimpleTestCase):
    def test_ok(self):
        result = calculate_status(Decimal('500'), Decimal('1000'), 80)
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['remaining'], Decimal('500'))

    def test_warning_at_threshold(self):
        result = calculate_status(Decimal('800'), Decimal('1000'), 80)
        self.assertEqual(result['status'], 'warning')

    def test_exceeded(self):
        result = calculate_status(Decimal('1200'), Decimal('1000'), 80)
        self.assertEqual(result['status'], 'exceeded')
        self.assertEqual(result['remaining'], Decimal('-200'))


class BudgetAPITests(APITestCase):
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
        self.year, self.month = current_jalali_month(self.today)
        self.client.force_authenticate(self.u1)

    def make_budget(self, user, category, limit=1000):
        return Budget.objects.create(
            user=user, category=category,
            year=self.year, month=self.month, limit_amount=limit,
        )

    def spend(self, user, category, amount, date=None):
        return Transaction.objects.create(
            user=user, category=category, amount=amount,
            date=date or self.today,
        )

    def test_create_budget_computes_gregorian_range(self):
        res = self.client.post('/api/budgets/', {
            'category': self.food.pk, 'year': self.year,
            'month': self.month, 'limit_amount': '1000000',
        })
        self.assertEqual(res.status_code, 201)
        budget = Budget.objects.get()
        self.assertEqual(budget.user, self.u1)
        start, end = jalali_month_range(self.year, self.month)
        self.assertEqual((budget.start_date, budget.end_date), (start, end))

    def test_gregorian_year_rejected(self):
        res = self.client.post('/api/budgets/', {
            'category': self.food.pk, 'year': 2026,
            'month': 11, 'limit_amount': '1000',
        })
        self.assertEqual(res.status_code, 400)

    def test_response_has_period_info(self):
        self.make_budget(self.u1, self.food)
        res = self.client.get('/api/budgets/')
        self.assertIn('period_label', res.data[0])
        self.assertIn('start_date', res.data[0])
        self.assertIn('end_date', res.data[0])

    def test_income_category_rejected(self):
        res = self.client.post('/api/budgets/', {
            'category': self.salary.pk, 'year': self.year,
            'month': self.month, 'limit_amount': '1000',
        })
        self.assertEqual(res.status_code, 400)

    def test_duplicate_budget_rejected(self):
        payload = {
            'category': self.food.pk, 'year': self.year,
            'month': self.month, 'limit_amount': '1000',
        }
        self.assertEqual(self.client.post('/api/budgets/', payload).status_code, 201)
        self.assertEqual(self.client.post('/api/budgets/', payload).status_code, 400)

    def test_list_only_own_budgets(self):
        self.make_budget(self.u1, self.food)
        self.make_budget(self.u2, self.food)
        res = self.client.get('/api/budgets/')
        self.assertEqual(len(res.data), 1)

    def test_cannot_access_other_users_budget(self):
        other = self.make_budget(self.u2, self.food)
        res = self.client.get(f'/api/budgets/{other.pk}/')
        self.assertEqual(res.status_code, 404)

    def test_spent_counts_only_matching_transactions(self):
        self.make_budget(self.u1, self.food)
        self.spend(self.u1, self.food, 300)
        start, end = jalali_month_range(self.year, self.month)
        self.spend(self.u1, self.food, 5000, start - timedelta(days=1))  # ماه قبل
        self.spend(self.u1, self.food, 5000, end + timedelta(days=1))    # ماه بعد
        self.spend(self.u2, self.food, 5000)                             # کاربر دیگر
        self.spend(self.u1, self.other, 5000)                            # دسته‌ی دیگر
        res = self.client.get('/api/budgets/')
        self.assertEqual(Decimal(str(res.data[0]['spent'])), Decimal('300'))
        self.assertEqual(res.data[0]['status'], 'ok')

    def test_alerts_endpoint_returns_only_problem_budgets(self):
        self.make_budget(self.u1, self.food)
        self.make_budget(self.u1, self.other)
        self.spend(self.u1, self.food, 900)
        self.spend(self.u1, self.other, 100)
        res = self.client.get('/api/budgets/alerts/')
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['status'], 'warning')