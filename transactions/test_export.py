import csv
import io

from rest_framework.test import APITestCase

from accounts.models import User
from categories.models import Category
from .models import Transaction


class ExportTests(APITestCase):
    def setUp(self):
        self.u1 = User.objects.create_user(
            username='u1', email='u1@example.com', password='Pass12345!x'
        )
        self.u2 = User.objects.create_user(
            username='u2', email='u2@example.com', password='Pass12345!x'
        )
        self.food = Category.objects.get(user=None, name='خوراک', type='expense')
        self.salary = Category.objects.get(user=None, name='حقوق', type='income')
        self.client.force_authenticate(self.u1)

    def add(self, user, category, amount, description=''):
        return Transaction.objects.create(
            user=user, category=category, amount=amount,
            date='2026-11-01', description=description,
        )

    def fetch(self, url='/api/transactions/export/'):
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        text = res.content.decode('utf-8-sig')
        return res, list(csv.reader(io.StringIO(text)))

    def test_export_has_header_and_only_own_rows(self):
        self.add(self.u1, self.food, 100, 'ناهار')
        self.add(self.u1, self.salary, 5000, 'حقوق ماهانه')
        self.add(self.u2, self.food, 999, 'مال کاربر دیگر')

        res, rows = self.fetch()
        self.assertEqual(rows[0], ['date', 'type', 'category', 'amount', 'description'])
        self.assertEqual(len(rows), 3)
        descriptions = {row[4] for row in rows[1:]}
        self.assertEqual(descriptions, {'ناهار', 'حقوق ماهانه'})

    def test_export_is_a_utf8_attachment_with_bom(self):
        self.add(self.u1, self.food, 100, 'ناهار')
        res, _ = self.fetch()
        self.assertTrue(res.content.startswith(b'\xef\xbb\xbf'))
        self.assertIn('attachment', res['Content-Disposition'])
        self.assertTrue(res['Content-Type'].startswith('text/csv'))

    def test_export_respects_filters(self):
        self.add(self.u1, self.food, 100, 'ناهار')
        self.add(self.u1, self.salary, 5000, 'حقوق ماهانه')
        _, rows = self.fetch('/api/transactions/export/?type=income')
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][1], 'income')

    def test_export_neutralizes_formulas(self):
        self.add(self.u1, self.food, 100, '=HYPERLINK("http://evil.example")')
        _, rows = self.fetch()
        self.assertTrue(rows[1][4].startswith("'="))

    def test_export_requires_authentication(self):
        self.client.force_authenticate(None)
        res = self.client.get('/api/transactions/export/')
        self.assertIn(res.status_code, (401, 403))