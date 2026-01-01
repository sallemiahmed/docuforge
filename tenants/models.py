"""
DocuForge Tenant Models

Multi-tenant support for SaaS deployment.
"""
from django.db import models


class Tenant(models.Model):
    """
    Represents a tenant (organization) in the multi-tenant system.

    Each tenant gets their own subdomain and isolated data.
    Example: acme.docuforge.com -> Tenant(subdomain='acme')
    """
    name = models.CharField(max_length=255)
    subdomain = models.CharField(max_length=63, unique=True, db_index=True)

    # Configuration
    is_active = models.BooleanField(default=True)
    max_templates = models.PositiveIntegerField(default=100)
    max_documents = models.PositiveIntegerField(default=10000)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.subdomain})"
