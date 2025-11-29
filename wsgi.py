"""WSGI entry point for Gunicorn."""
import os
from app import create_app

# Use production config for deployment
app = create_app(os.environ.get('FLASK_ENV', 'production'))
