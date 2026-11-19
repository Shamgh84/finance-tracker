from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from budgets.models import Budget
from categories.models import Category
from config.jalali import current_jalali_month
from transactions.models import Transaction
from goals.models import Goal


class SeedDemoTests(TestCase):
    def run_command(self):
        call_command('seed_demo', stdout=StringIO())

    def test_creates_demo_user_with_data(self):
        self.run_command()
        user = User.objects.get(username='demo')
        self.assertTrue(user.check_password('Demo@12345'))
        self.assertGreater(Transaction.objects.filter(user=user).count(), 20)
        year, month = current_jalali_month(timezone.localdate())
        budgets = Budget.objects.filter(user=user, year=year, month=month)
        self.assertEqual(budgets.count(), 4)
        self.assertEqual(Goal.objects.filter(user=user).count(), 3)

    def test_no_future_transactions(self):
        self.run_command()
        latest = Transaction.objects.order_by('-date').first()
        self.assertLessEqual(latest.date, timezone.localdate())

    def test_is_repeatable(self):
        self.run_command()
        first = Transaction.objects.count()
        self.run_command()
        self.assertEqual(User.objects.filter(username='demo').count(), 1)
        self.assertEqual(Transaction.objects.count(), first)

    def test_does_not_touch_other_users(self):
        other = User.objects.create_user(username='x', email='x@example.com', password='Pass12345!x')
        category = Category.objects.filter(user=None, type='expense').first()
        Transaction.objects.create(user=other, category=category, amount=100, date=timezone.localdate())
        self.run_command()
        self.assertEqual(Transaction.objects.filter(user=other).count(), 1)