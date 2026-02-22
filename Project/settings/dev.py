"""
Django Settings - Development Configuration
Local development environment settings
"""

from .base import *
from decouple import config

# ==================== DEBUG MODE ====================
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']

# ==================== DATABASE - SQLite for Development ====================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ==================== SECURITY (RELAXED FOR DEV) ====================
SESSION_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
CSRF_COOKIE_SECURE = False

# ==================== INSTALLED APPS - DEV TOOLS ====================
INSTALLED_APPS += [
    'debug_toolbar',      # Debug toolbar
]

# ==================== MIDDLEWARE - DEV TOOLS ====================
MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

# ==================== DEBUG TOOLBAR ====================
INTERNAL_IPS = [
    '127.0.0.1',
]

# ==================== LOGGING - VERBOSE ====================
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['core']['level'] = 'DEBUG'

# ==================== EMAIL - Console Backend (Dev) ====================
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ==================== CORS - Allow All (Dev Only) ====================
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:8000',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:8000',
]

# ==================== CACHE - Memory (Dev) ====================
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# ==================== REST FRAMEWORK - Dev Settings ====================
REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES'] = [
    'rest_framework.permissions.AllowAny',  # Dev only
]

print("✅ Django Development Settings Loaded")
