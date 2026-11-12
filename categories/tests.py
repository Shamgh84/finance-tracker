from rest_framework.test import APITestCase

from accounts.models import User
from .models import Category


class CategoryAPITests(APITestCase):
    def setUp(self):
        self.u1 = User.objects.create_user(
            username='u1', email='u1@example.com', password='Pass12345!x'
        )
        self.u2 = User.objects.create_user(
            username='u2', email='u2@example.com', password='Pass12345!x'
        )
        self.mine = Category.objects.create(user=self.u1, name='ورزش', type='expense')
        self.theirs = Category.objects.create(user=self.u2, name='کتاب', type='expense')
        self.client.force_authenticate(self.u1)

    def test_list_shows_defaults_and_own_only(self):
        res = self.client.get('/api/categories/')
        names = [c['name'] for c in res.data]
        self.assertIn('ورزش', names)
        self.assertIn('خوراک', names)
        self.assertNotIn('کتاب', names)

    def test_cannot_access_other_users_category(self):
        res = self.client.get(f'/api/categories/{self.theirs.pk}/')
        self.assertEqual(res.status_code, 404)

    def test_cannot_edit_default_category(self):
        default = Category.objects.get(user=None, name='خوراک', type='expense')
        res = self.client.patch(f'/api/categories/{default.pk}/', {'name': 'x'})
        self.assertEqual(res.status_code, 403)

    def test_create_assigns_current_user(self):
        res = self.client.post(
            '/api/categories/', {'name': 'سفر', 'type': 'expense'}
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Category.objects.get(name='سفر').user, self.u1)

    def test_duplicate_of_default_rejected(self):
        res = self.client.post(
            '/api/categories/', {'name': 'خوراک', 'type': 'expense'}
        )
        self.assertEqual(res.status_code, 400)