from rest_framework.test import APIClient, APITestCase

from .models import User


class AuthAPITests(APITestCase):
    def test_register_works_even_with_active_session(self):
        # کاربری که در همان مرورگر با admin وارد شده، نباید با خطای CSRF روبه‌رو شود
        admin = User.objects.create_user(
            username='admin1', email='admin1@example.com', password='Pass12345!x'
        )
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(admin)
        res = client.post('/api/auth/register/', {
            'username': 'newuser', 'email': 'new@example.com',
            'password': 'Str0ng!Pass99', 'password2': 'Str0ng!Pass99',
        })
        self.assertEqual(res.status_code, 201)

    def test_register_rejects_mismatched_passwords(self):
        res = self.client.post('/api/auth/register/', {
            'username': 'x', 'email': 'x@example.com',
            'password': 'Str0ng!Pass99', 'password2': 'Different!Pass1',
        })
        self.assertEqual(res.status_code, 400)

    def test_login_returns_tokens(self):
        User.objects.create_user(
            username='u1', email='u1@example.com', password='Pass12345!x'
        )
        res = self.client.post(
            '/api/auth/login/', {'username': 'u1', 'password': 'Pass12345!x'}
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)

    def test_me_requires_authentication(self):
        res = self.client.get('/api/auth/me/')
        self.assertEqual(res.status_code, 401)

    def test_frontend_pages_load(self):
        for url in ('/', '/login/', '/register/', '/transactions/'):
            self.assertEqual(self.client.get(url).status_code, 200)