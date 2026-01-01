"""
Tests for DocuForge Tenant Middleware
"""
import uuid
from django.test import TestCase
from tenants.models import Tenant


class TestTenantModel(TestCase):
    """Tests for Tenant model."""

    def test_create_tenant(self):
        """Test creating a tenant."""
        subdomain = f"test{uuid.uuid4().hex[:8]}"
        tenant = Tenant.objects.create(
            name='Test Corp',
            subdomain=subdomain,
            is_active=True
        )
        self.assertEqual(tenant.name, 'Test Corp')
        self.assertTrue(tenant.is_active)

    def test_default_limits(self):
        """Test default template and document limits."""
        subdomain = f"limits{uuid.uuid4().hex[:8]}"
        tenant = Tenant.objects.create(
            name='Test Corp',
            subdomain=subdomain
        )
        self.assertEqual(tenant.max_templates, 100)
        self.assertEqual(tenant.max_documents, 10000)
