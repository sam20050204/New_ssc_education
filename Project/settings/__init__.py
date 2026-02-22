"""
Django settings package for SSC Education Project.

The settings are split into:
- base.py: Shared configuration for all environments
- dev.py: Development-specific settings (DEBUG=True, SQLite)
- prod.py: Production-specific settings (DEBUG=False, PostgreSQL)

Usage:
- Development: DJANGO_SETTINGS_MODULE=Project.settings.dev python manage.py runserver
- Production: DJANGO_SETTINGS_MODULE=Project.settings.prod gunicorn Project.wsgi
- Default: Uses dev.py for development
"""

import os

# Determine which settings module to use based on environment
ENV = os.environ.get('ENVIRONMENT', 'dev').lower()

if ENV == 'production' or ENV == 'prod':
    from .prod import *  # noqa
else:
    from .dev import *  # noqa
