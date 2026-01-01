"""
Tests for DocuForge API Views

Tests the REST API endpoints for template rendering and validation.
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status


class TestHealthCheck(TestCase):
    """Tests for health check endpoint."""

    def setUp(self):
        self.client = APIClient()

    def test_health_check_returns_200(self):
        """Test that health check returns 200 OK."""
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health_check_returns_healthy_status(self):
        """Test that health check returns healthy status."""
        response = self.client.get('/api/health/')
        self.assertEqual(response.data['status'], 'healthy')


class TestAPIInfo(TestCase):
    """Tests for API info endpoint."""

    def setUp(self):
        self.client = APIClient()

    def test_api_info_returns_200(self):
        """Test that API info returns 200 OK."""
        response = self.client.get('/api/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_api_info_returns_endpoints(self):
        """Test that API info lists available endpoints."""
        response = self.client.get('/api/')
        self.assertIn('endpoints', response.data)


class TestRenderEndpoint(TestCase):
    """Tests for template render endpoint."""

    def setUp(self):
        self.client = APIClient()

    def test_render_simple_template(self):
        """Test rendering a simple template."""
        response = self.client.post('/api/render/', {
            'template': 'Hello {{name}}!',
            'context': {'name': 'World'}
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['content'], 'Hello World!')

    def test_render_with_list_variable(self):
        """Test rendering with list variable."""
        response = self.client.post('/api/render/', {
            'template': 'Items: {{items}}',
            'context': {'items': ['Apple', 'Orange', 'Banana']}
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Apple', response.data['content'])

    def test_render_with_conditional(self):
        """Test rendering with conditional block."""
        response = self.client.post('/api/render/', {
            'template': '{% if show %}Visible{% endif %}',
            'context': {'show': True}
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['content'], 'Visible')


class TestValidateEndpoint(TestCase):
    """Tests for template validation endpoint."""

    def setUp(self):
        self.client = APIClient()

    def test_validate_valid_template(self):
        """Test validating a valid template."""
        response = self.client.post('/api/validate/', {
            'template': 'Hello {{name}}!'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['valid'])

    def test_validate_returns_variables(self):
        """Test that validation returns list of variables."""
        response = self.client.post('/api/validate/', {
            'template': '{{a}} {{b}} {{c}}'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data['variables']), {'a', 'b', 'c'})


class TestConditionTestEndpoint(TestCase):
    """Tests for condition test endpoint."""

    def setUp(self):
        self.client = APIClient()

    def test_condition_true(self):
        """Test condition that evaluates to true."""
        response = self.client.post('/api/test-condition/', {
            'condition': 'age >= 18',
            'context': {'age': 21}
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['result'])

    def test_condition_false(self):
        """Test condition that evaluates to false."""
        response = self.client.post('/api/test-condition/', {
            'condition': 'age >= 18',
            'context': {'age': 16}
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['result'])

    def test_and_or_precedence(self):
        """Test AND/OR precedence in condition."""
        response = self.client.post('/api/test-condition/', {
            'condition': 'A AND B OR C',
            'context': {'A': False, 'B': True, 'C': True}
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['result'])
