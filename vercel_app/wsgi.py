"""
Vercel WSGI Handler for DocuForge

This module configures Django for serverless deployment on Vercel.
"""
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'docuforge.settings')

from django.core.wsgi import get_wsgi_application

app = get_wsgi_application()
