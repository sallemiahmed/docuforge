"""
DocuForge Tenant Middleware

Extracts tenant from subdomain and attaches to request.
This enables automatic tenant scoping for all queries.

Example:
    acme.docuforge.com -> request.tenant = Tenant(subdomain='acme')
    jones.docuforge.com -> request.tenant = Tenant(subdomain='jones')
"""
from django.http import HttpResponseNotFound

from .models import Tenant


class TenantMiddleware:
    """
    Middleware to identify tenant from subdomain.

    Usage:
        Add to MIDDLEWARE in settings.py after AuthenticationMiddleware.

    The tenant is then available as request.tenant in views.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extract subdomain from host
        host = request.get_host().split(':')[0]  # Remove port if present
        parts = host.split('.')

        # Default: no tenant (main site)
        request.tenant = None
        request.tenant_id = None

        # Check for subdomain (e.g., acme.docuforge.com has 3 parts)
        if len(parts) >= 3:
            subdomain = parts[0]

            # Skip common non-tenant subdomains
            if subdomain not in ('www', 'api', 'admin', 'localhost'):
                try:
                    tenant = Tenant.objects.get(subdomain=subdomain, is_active=True)
                    request.tenant = tenant
                    request.tenant_id = tenant.subdomain
                except Tenant.DoesNotExist:
                    # For strict multi-tenancy, you could return 404 here
                    # return HttpResponseNotFound("Tenant not found")
                    pass

        # Also check for tenant in header (useful for API testing)
        if not request.tenant and 'X-Tenant-ID' in request.headers:
            tenant_id = request.headers['X-Tenant-ID']
            try:
                tenant = Tenant.objects.get(subdomain=tenant_id, is_active=True)
                request.tenant = tenant
                request.tenant_id = tenant.subdomain
            except Tenant.DoesNotExist:
                pass

        return self.get_response(request)


class TenantQuerySetMixin:
    """
    Mixin for querysets to automatically filter by tenant.

    Usage:
        class MyModel(models.Model):
            tenant_id = models.CharField(max_length=100)

        class MyModelManager(TenantQuerySetMixin, models.Manager):
            pass
    """

    def for_tenant(self, tenant_id):
        """Filter queryset to a specific tenant."""
        return self.filter(tenant_id=tenant_id)

    def for_request(self, request):
        """Filter queryset based on request's tenant."""
        if hasattr(request, 'tenant_id') and request.tenant_id:
            return self.filter(tenant_id=request.tenant_id)
        return self.all()
