"""
DocuForge API Views

REST API endpoints for template management and document generation.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response

from core.models import Template, Document
from core.parser import (
    TemplateEngine,
    ConditionEvaluator,
    TemplateEngineError,
    ConditionEvaluationError,
)
from .serializers import (
    TemplateSerializer,
    TemplateValidationSerializer,
    RenderRequestSerializer,
    RenderResponseSerializer,
    ConditionTestSerializer,
    DocumentSerializer,
)


class TemplateViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for templates.

    list:   GET /api/templates/
    create: POST /api/templates/
    read:   GET /api/templates/{id}/
    update: PUT /api/templates/{id}/
    delete: DELETE /api/templates/{id}/
    """
    queryset = Template.objects.filter(is_active=True)
    serializer_class = TemplateSerializer

    def get_queryset(self):
        """Filter by tenant if present."""
        queryset = super().get_queryset()
        if hasattr(self.request, 'tenant_id') and self.request.tenant_id:
            queryset = queryset.filter(tenant_id=self.request.tenant_id)
        return queryset

    def perform_create(self, serializer):
        """Set tenant_id on create."""
        tenant_id = getattr(self.request, 'tenant_id', None)
        serializer.save(tenant_id=tenant_id)

    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        """Validate a stored template."""
        template = self.get_object()
        engine = TemplateEngine()
        result = engine.validate(template.content)
        return Response(result)


class DocumentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only operations for generated documents.

    list: GET /api/documents/
    read: GET /api/documents/{id}/
    """
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    def get_queryset(self):
        """Filter by tenant if present."""
        queryset = super().get_queryset()
        if hasattr(self.request, 'tenant_id') and self.request.tenant_id:
            queryset = queryset.filter(tenant_id=self.request.tenant_id)
        return queryset


@api_view(['POST'])
def render_template(request):
    """
    Render a template with provided context.

    POST /api/render/

    Request body:
    {
        "template": "Hello {{name}}, your items: {{items}}",
        "context": {
            "name": "John",
            "items": ["Apple", "Orange"]
        },
        "save": false
    }

    OR use a stored template:
    {
        "template_id": 1,
        "context": {...},
        "save": true,
        "title": "Document Title"
    }
    """
    serializer = RenderRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    engine = TemplateEngine()

    # Get template content
    if data.get('template_id'):
        try:
            template_obj = Template.objects.get(id=data['template_id'], is_active=True)
            template_content = template_obj.content
        except Template.DoesNotExist:
            return Response(
                {'error': 'Template not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        template_content = data['template']
        template_obj = None

    context = data['context']

    try:
        # Render the template
        rendered_content = engine.render(template_content, context)

        # Get metadata
        variables = engine.get_variables(template_content)
        conditions = engine.get_conditions(template_content)

        response_data = {
            'content': rendered_content,
            'document_id': None,
            'variables_used': variables,
            'conditions_evaluated': conditions,
        }

        # Save as document if requested
        if data.get('save'):
            tenant_id = getattr(request, 'tenant_id', None)
            document = Document.objects.create(
                template=template_obj,
                title=data['title'],
                content=rendered_content,
                context_data=context,
                tenant_id=tenant_id,
            )
            response_data['document_id'] = document.id

        return Response(response_data)

    except TemplateEngineError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
def validate_template(request):
    """
    Validate template syntax without rendering.

    POST /api/validate/

    Request body:
    {
        "template": "Hello {{name}}"
    }
    """
    serializer = TemplateValidationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    engine = TemplateEngine()
    result = engine.validate(serializer.validated_data['template'])

    return Response(result)


@api_view(['POST'])
def test_condition(request):
    """
    Test a condition expression against a context.

    POST /api/test-condition/

    Request body:
    {
        "condition": "age >= 18 AND has_consent",
        "context": {
            "age": 25,
            "has_consent": true
        }
    }

    This endpoint is useful for debugging conditional logic
    and understanding how conditions will evaluate.
    """
    serializer = ConditionTestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    evaluator = ConditionEvaluator()

    try:
        result = evaluator.evaluate(data['condition'], data['context'])
        return Response({
            'condition': data['condition'],
            'context': data['context'],
            'result': result,
            'explanation': f"Condition evaluated to {result}"
        })
    except ConditionEvaluationError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint.

    GET /api/health/
    """
    return Response({
        'status': 'healthy',
        'service': 'DocuForge Template Engine',
        'version': '1.0.0',
    })


@api_view(['GET'])
def api_info(request):
    """
    API information and documentation.

    GET /api/
    """
    return Response({
        'name': 'DocuForge API',
        'version': '1.0.0',
        'description': 'Document generation engine with custom template syntax',
        'endpoints': {
            'health': '/api/health/',
            'templates': '/api/templates/',
            'documents': '/api/documents/',
            'render': '/api/render/',
            'validate': '/api/validate/',
            'test_condition': '/api/test-condition/',
        },
        'template_syntax': {
            'variables': '{{variable_name}}',
            'conditionals': '{% if condition %}...{% endif %}',
            'conditionals_else': '{% if condition %}...{% else %}...{% endif %}',
            'sections': '{% section name %}...{% endsection %}',
            'includes': '{% include section_name %}',
        },
        'supported_types': {
            'None': 'Converts to empty string',
            'str': 'Used as-is (stripped)',
            'int/float': 'Converted to string',
            'bool': 'Converted to Yes/No',
            'list/tuple': 'Joined with commas',
        },
        'condition_operators': {
            'comparison': ['==', '!=', '<', '<=', '>', '>='],
            'logical': ['AND', 'OR', 'NOT'],
            'precedence': 'NOT > AND > OR (standard)',
        }
    })
