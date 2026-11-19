from datetime import date
from decimal import Decimal

from django.test import SimpleTestCase
from rest_framework.test import APITestCase

from accounts.models import User
from .models import Goal
from .services import calculate_progress


class ProgressTests(SimpleTestCase):
    today = date(2026, 11, 14)

    def test_active_goal_with_monthly_amount(self):
        result = calculate_progress(
            Decimal('1000000'), Decimal('4000000'), date(2027, 2, 12), self.today
        )
        self.assertEqual(result['status'], 'active')
        self.assertEqual(result['percent'], Decimal('25.0'))
        self.assertEqual(result['remaining'], Decimal('3000000'))
        self.assertEqual(result['days_left'], 90)
        self.assertEqual(result['monthly_needed'], Decimal('1000000.00'))

    def test_completed_goal(self):
        result = calculate_progress(
            Decimal('5000000'), Decimal('4000000'), date(2027, 2, 12), self.today
        )
        self.assertEqual(result['status'], 'done')
        self.assertEqual(result['remaining'], Decimal('0'))
        self.assertIsNone(result['monthly_needed'])

    def test_overdue_goal(self):
        result = calculate_progress(
            Decimal('1000000'), Decimal('4000000'), date(2026, 11, 1), self.today
        )
        self.assertEqual(result['status'], 'overdue')
        self.assertEqual(result['days_left'], -13)

    def test_goal_without_deadline(self):
        result = calculate_progress(Decimal('1000000'), Decimal('4000000'), None, self.today)
        self.assertEqual(result['status'], 'active')
        self.assertIsNone(result['days_left'])
        self.assertIsNone(result['monthly_needed'])

    def test_close_deadline_counts_as_one_month(self):
        result = calculate_progress(
            Decimal('0'), Decimal('3000000'), date(2026, 11, 24), self.today
        )
        self.assertEqual(result['monthly_needed'], Decimal('3000000.00'))


class GoalAPITests(APITestCase):
    def setUp(self):
        self.u1 = User.objects.create_user(
            username='u1', email='u1@example.com', password='Pass12345!x'
        )
        self.u2 = User.objects.create_user(
            username='u2', email='u2@example.com', password='Pass12345!x'
        )
        self.client.force_authenticate(self.u1)

    def make(self, user, name='لپ‌تاپ', target=1000):
        return Goal.objects.create(user=user, name=name, target_amount=target)

    def contribute(self, goal, amount):
        return self.client.post(f'/api/goals/{goal.pk}/contribute/', {'amount': amount})

    def test_create_assigns_current_user(self):
        res = self.client.post('/api/goals/', {'name': 'سفر', 'target_amount': '5000000'})
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Goal.objects.get().user, self.u1)
        self.assertEqual(res.data['saved'], Decimal('0'))
        self.assertEqual(res.data['status'], 'active')

    def test_blank_name_rejected(self):
        res = self.client.post('/api/goals/', {'name': '   ', 'target_amount': '1000'})
        self.assertEqual(res.status_code, 400)

    def test_list_only_own_goals(self):
        self.make(self.u1)
        self.make(self.u2)
        res = self.client.get('/api/goals/')
        self.assertEqual(len(res.data), 1)

    def test_cannot_access_other_users_goal(self):
        other = self.make(self.u2)
        self.assertEqual(self.client.get(f'/api/goals/{other.pk}/').status_code, 404)
        self.assertEqual(self.contribute(other, '100').status_code, 404)

    def test_deposit_and_withdraw(self):
        goal = self.make(self.u1, target=1000)
        res = self.contribute(goal, '300')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['saved'], Decimal('300'))
        res = self.contribute(goal, '-100')
        self.assertEqual(res.data['saved'], Decimal('200'))
        self.assertEqual(res.data['percent'], Decimal('20.0'))

    def test_withdraw_more_than_saved_rejected(self):
        goal = self.make(self.u1)
        self.contribute(goal, '100')
        res = self.contribute(goal, '-500')
        self.assertEqual(res.status_code, 400)
        saved = self.client.get(f'/api/goals/{goal.pk}/').data['saved']
        self.assertEqual(saved, Decimal('100'))

    def test_zero_amount_rejected(self):
        goal = self.make(self.u1)
        self.assertEqual(self.contribute(goal, '0').status_code, 400)

    def test_goal_becomes_done(self):
        goal = self.make(self.u1, target=1000)
        res = self.contribute(goal, '1000')
        self.assertEqual(res.data['status'], 'done')

    def test_delete_goal(self):
        goal = self.make(self.u1)
        self.contribute(goal, '100')
        self.assertEqual(self.client.delete(f'/api/goals/{goal.pk}/').status_code, 204)
        self.assertEqual(Goal.objects.count(), 0)

    def test_requires_authentication(self):
        self.client.force_authenticate(None)
        self.assertIn(self.client.get('/api/goals/').status_code, (401, 403))
