"""
DocuForge API URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'templates', views.TemplateViewSet)
router.register(r'documents', views.DocumentViewSet)

urlpatterns = [
    path('', views.api_info, name='api-info'),
    path('health/', views.health_check, name='health-check'),
    path('render/', views.render_template, name='render-template'),
    path('validate/', views.validate_template, name='validate-template'),
    path('test-condition/', views.test_condition, name='test-condition'),
    path('', include(router.urls)),
]
