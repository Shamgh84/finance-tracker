from rest_framework.test import APITestCase

from accounts.models import User
from categories.models import Category
from .models import Transaction


class TransactionAPITests(APITestCase):
    def setUp(self):
        self.u1 = User.objects.create_user(
            username='u1', email='u1@example.com', password='Pass12345!x'
        )
        self.u2 = User.objects.create_user(
            username='u2', email='u2@example.com', password='Pass12345!x'
        )
        self.food = Category.objects.get(user=None, name='خوراک', type='expense')
        self.salary = Category.objects.get(user=None, name='حقوق', type='income')
        self.u2_cat = Category.objects.create(user=self.u2, name='کتاب', type='expense')
        self.client.force_authenticate(self.u1)

    def make(self, user, category, amount, date, description=''):
        return Transaction.objects.create(
            user=user, category=category, amount=amount,
            date=date, description=description,
        )

    def test_create_assigns_current_user(self):
        res = self.client.post('/api/transactions/', {
            'category': self.food.pk, 'amount': '150000',
            'date': '2026-11-01', 'description': 'ناهار',
        })
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Transaction.objects.get().user, self.u1)

    def test_list_only_own_transactions(self):
        self.make(self.u1, self.food, 100, '2026-11-01')
        self.make(self.u2, self.food, 200, '2026-11-01')
        res = self.client.get('/api/transactions/')
        self.assertEqual(res.data['count'], 1)

    def test_cannot_access_other_users_transaction(self):
        other = self.make(self.u2, self.food, 200, '2026-11-01')
        res = self.client.get(f'/api/transactions/{other.pk}/')
        self.assertEqual(res.status_code, 404)

    def test_cannot_use_other_users_category(self):
        res = self.client.post('/api/transactions/', {
            'category': self.u2_cat.pk, 'amount': '100', 'date': '2026-11-01',
        })
        self.assertEqual(res.status_code, 400)

    def test_negative_amount_rejected(self):
        res = self.client.post('/api/transactions/', {
            'category': self.food.pk, 'amount': '-5', 'date': '2026-11-01',
        })
        self.assertEqual(res.status_code, 400)

    def test_filter_by_type_and_date(self):
        self.make(self.u1, self.food, 100, '2026-11-01')
        self.make(self.u1, self.salary, 5000, '2026-10-01')
        res = self.client.get('/api/transactions/?type=income')
        self.assertEqual(res.data['count'], 1)
        res = self.client.get('/api/transactions/?date_from=2026-11-01')
        self.assertEqual(res.data['count'], 1)

    def test_search_description(self):
        self.make(self.u1, self.food, 100, '2026-11-01', 'پیتزا')
        self.make(self.u1, self.food, 100, '2026-11-02', 'نان')
        res = self.client.get('/api/transactions/?search=پیتزا')
        self.assertEqual(res.data['count'], 1)

    def test_delete_own_transaction(self):
        t = self.make(self.u1, self.food, 100, '2026-11-01')
        res = self.client.delete(f'/api/transactions/{t.pk}/')
        self.assertEqual(res.status_code, 204)