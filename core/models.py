"""
DocuForge Core Models

Models for template and document storage.
"""
from django.db import models
from django.utils import timezone


class Template(models.Model):
    """
    A document template with custom syntax.

    Templates use DocuForge's custom syntax:
    - Variables: {{variable_name}}
    - Conditionals: {% if condition %}...{% endif %}
    - Sections: {% section name %}...{% endsection %}
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    content = models.TextField()

    # Metadata
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Optional tenant association
    tenant_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['slug', 'tenant_id']),
        ]

    def __str__(self):
        return f"{self.name} (v{self.version})"


class Document(models.Model):
    """
    A generated document from a template.
    """
    template = models.ForeignKey(
        Template,
        on_delete=models.SET_NULL,
        null=True,
        related_name='documents'
    )
    title = models.CharField(max_length=255)

    # The rendered content
    content = models.TextField()

    # The context used to render (stored for audit/debugging)
    context_data = models.JSONField(default=dict)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    tenant_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
