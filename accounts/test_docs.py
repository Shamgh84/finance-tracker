from rest_framework.test import APITestCase


class ApiDocsTests(APITestCase):
    def test_schema_is_generated_and_lists_main_endpoints(self):
        res = self.client.get('/api/schema/?format=json')
        self.assertEqual(res.status_code, 200)
        paths = res.json()['paths']
        for path in (
            '/api/auth/login/',
            '/api/transactions/',
            '/api/transactions/export/',
            '/api/budgets/',
            '/api/analytics/report/',
        ):
            self.assertIn(path, paths)

    def test_swagger_page_loads(self):
        self.assertEqual(self.client.get('/api/docs/').status_code, 200)