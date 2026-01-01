"""DocuForge URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.shortcuts import render
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


def home(request):
    """Landing page with test UI."""
    return render(request, 'index.html')


def api_info(request):
    """API info endpoint."""
    return JsonResponse({
        'name': 'DocuForge API',
        'version': '1.0.0',
        'description': 'Custom Document Generation Engine with Type-Safe Template Processing',
        'author': 'Ahmed Sallemi | MediaTree',
        'endpoints': {
            'api_root': '/api/',
            'health': '/api/health/',
            'render': '/api/render/',
            'validate': '/api/validate/',
            'test_condition': '/api/test-condition/',
            'docs': '/docs/',
            'swagger': '/swagger/',
        },
        'github': 'https://github.com/sallemiahmed/docuforge',
    })


urlpatterns = [
    path('', home, name='home'),
    path('api-info/', api_info, name='api-info'),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
