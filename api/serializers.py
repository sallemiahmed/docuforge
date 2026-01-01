"""
DocuForge API Serializers
"""
from rest_framework import serializers

from core.models import Template, Document


class TemplateSerializer(serializers.ModelSerializer):
    """Serializer for Template model."""

    class Meta:
        model = Template
        fields = [
            'id', 'name', 'slug', 'description', 'content',
            'version', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TemplateValidationSerializer(serializers.Serializer):
    """Serializer for template validation requests."""
    template = serializers.CharField(required=True)


class RenderRequestSerializer(serializers.Serializer):
    """Serializer for document render requests."""
    template = serializers.CharField(required=False, help_text="Template content (if not using template_id)")
    template_id = serializers.IntegerField(required=False, help_text="ID of stored template")
    context = serializers.DictField(required=True, help_text="Variables for substitution")
    save = serializers.BooleanField(default=False, help_text="Save as document")
    title = serializers.CharField(required=False, help_text="Document title (required if save=True)")

    def validate(self, data):
        if not data.get('template') and not data.get('template_id'):
            raise serializers.ValidationError(
                "Either 'template' or 'template_id' must be provided"
            )
        if data.get('save') and not data.get('title'):
            raise serializers.ValidationError(
                "'title' is required when save=True"
            )
        return data


class RenderResponseSerializer(serializers.Serializer):
    """Serializer for render response."""
    content = serializers.CharField()
    document_id = serializers.IntegerField(required=False, allow_null=True)
    variables_used = serializers.ListField(child=serializers.CharField())
    conditions_evaluated = serializers.ListField(child=serializers.CharField())


class ConditionTestSerializer(serializers.Serializer):
    """Serializer for condition testing requests."""
    condition = serializers.CharField(required=True)
    context = serializers.DictField(required=True)


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model."""
    template_name = serializers.CharField(source='template.name', read_only=True)

    class Meta:
        model = Document
        fields = [
            'id', 'template', 'template_name', 'title',
            'content', 'context_data', 'created_at'
        ]
        read_only_fields = ['id', 'content', 'created_at']
