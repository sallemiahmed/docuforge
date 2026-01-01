"""
Pytest configuration for DocuForge tests.
"""
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django before importing anything else
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'docuforge.settings')

import django
django.setup()

import pytest

@pytest.fixture(scope='session')
def django_db_setup():
    """Setup test database."""
    pass
