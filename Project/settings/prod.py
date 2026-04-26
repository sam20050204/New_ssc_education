"""
Django Settings - Production Configuration
Production environment with strict security settings
"""

from .base import *
from decouple import config

# ==================== DEBUG MODE ====================
DEBUG = False
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='yourdomain.com').split(',')
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='https://yourdomain.com'
).split(',')

# ==================== DATABASE - PostgreSQL for Production ====================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='ssc_education_db'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'ATOMIC_REQUESTS': True,
        'CONN_MAX_AGE': 600,
    }
}

# ==================== SECURITY - STRICT PRODUCTION ====================
SECRET_KEY = config('SECRET_KEY')  # Must be set in environment
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ==================== INSTALLED APPS ====================
INSTALLED_APPS = [app for app in INSTALLED_APPS if app not in ['debug_toolbar', 'django_extensions']]

# ==================== MIDDLEWARE ====================
MIDDLEWARE = [m for m in MIDDLEWARE if m != 'debug_toolbar.middleware.DebugToolbarMiddleware']

# ==================== EMAIL - SendGrid/SMTP ====================
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.smtp.EmailBackend'
)
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

# ==================== ADMIN NOTIFICATIONS ====================
ADMINS = [
    tuple(item.split(':', 1))
    for item in config('ADMINS', default='').split(',')
    if ':' in item
]

# ==================== LOGGING - ERROR FOCUSED ====================
LOGGING['loggers']['django']['level'] = 'WARNING'
LOGGING['loggers']['core']['level'] = 'INFO'

# ==================== CORS - Specific Origins ====================
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='https://yourdomain.com'
).split(',')

# ==================== CACHE - Redis ====================
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# ==================== STATIC FILES - CDN ====================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ==================== REST FRAMEWORK - Strict Permissions ====================
REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES'] = [
    'rest_framework.permissions.IsAuthenticated',
]
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = [
    'rest_framework.throttling.AnonRateThrottle',
    'rest_framework.throttling.UserRateThrottle',
]
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '100/hour',
    'user': '1000/hour',
}

# ==================== SENTRY - Error Tracking ====================
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=config('SENTRY_DSN', default=''),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=False
)
