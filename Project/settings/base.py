"""
Django Settings - Base Configuration
Shared settings for all environments
"""

import os
import secrets
from pathlib import Path
from decouple import config

# ==================== BASE DIRECTORY ====================
BASE_DIR = Path(__file__).resolve().parent.parent.parent


def parse_bool(value, default=False):
    """Parse common truthy/falsy env values without crashing on loose strings."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value

    normalized = str(value).strip().lower()
    if normalized in {'1', 'true', 't', 'yes', 'y', 'on', 'debug', 'dev', 'development'}:
        return True
    if normalized in {'0', 'false', 'f', 'no', 'n', 'off', 'prod', 'production', 'release'}:
        return False
    return default


def parse_csv(value):
    return [item.strip() for item in str(value).split(',') if item.strip()]


def get_local_secret_key():
    """Persist a local secret key so local sessions remain valid across restarts."""
    secret_key = config('SECRET_KEY', default='').strip()
    if secret_key:
        return secret_key

    secret_file = BASE_DIR / '.django_secret_key'
    if secret_file.exists():
        return secret_file.read_text(encoding='utf-8').strip()

    generated = secrets.token_urlsafe(50)
    secret_file.write_text(generated, encoding='utf-8')

    try:
        os.chmod(secret_file, 0o600)
    except OSError:
        pass

    return generated

# ==================== SECURITY (SET IN ENV) ====================
SECRET_KEY = get_local_secret_key()
DEBUG = parse_bool(config('DEBUG', default='false'), default=False)
ALLOWED_HOSTS = parse_csv(config('ALLOWED_HOSTS', default='localhost,127.0.0.1'))

# ==================== INSTALLED APPS ====================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',  # Django REST Framework
    'corsheaders',     # CORS support
    'django_extensions',  # Management commands
    
    # Local apps
    'core.apps.CoreConfig',
]

# ==================== MIDDLEWARE ====================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.LoggingMiddleware',  # Custom logging
    'core.middleware.SessionTimeoutMiddleware',
]

# ==================== URL CONFIGURATION ====================
ROOT_URLCONF = 'Project.urls'
WSGI_APPLICATION = 'Project.wsgi.application'

# ==================== TEMPLATES ====================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.static_version',  # Custom context
                'core.context_processors.collaboration_context',
            ],
        },
    },
]

# ==================== DATABASE (OVERRIDE IN ENV-SPECIFIC) ====================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ==================== PASSWORD VALIDATION ====================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ==================== INTERNATIONALIZATION ====================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# ==================== STATIC FILES ====================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_VERSION = '1.1'  # Increment for cache busting

# ==================== MEDIA FILES ====================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ==================== DEFAULT PRIMARY KEY ====================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==================== LOGGING CONFIGURATION ====================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '[{levelname}] {asctime} - {name}: {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': 'DEBUG',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
            'level': 'INFO',
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'errors.log',
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 5,
            'formatter': 'verbose',
            'level': 'ERROR',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'core': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# ==================== REST FRAMEWORK CONFIGURATION ====================
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# ==================== CORS CONFIGURATION ====================
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000',
    cast=parse_csv
)

# ==================== CACHE CONFIGURATION ====================
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'ssc-education-cache',
    }
}

# ==================== SESSION CONFIGURATION ====================
SESSION_COOKIE_SECURE = False  # Override in prod
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_SAVE_EVERY_REQUEST = True
SESSION_IDLE_TIMEOUT = config('SESSION_IDLE_TIMEOUT', default=1800, cast=int)
LOGIN_FAILURE_LIMIT = config('LOGIN_FAILURE_LIMIT', default=5, cast=int)
LOGIN_FAILURE_WINDOW = config('LOGIN_FAILURE_WINDOW', default=900, cast=int)
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
X_FRAME_OPTIONS = 'DENY'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# ==================== SECURITY HEADERS ====================
SECURE_BROWSER_XSS_FILTER = True
SECURE_REFERRER_POLICY = 'same-origin'
SECURE_CONTENT_SECURITY_POLICY = {
    'default-src': ("'self'",),
    # Existing templates still use inline scripts/styles; keep them allowed until
    # those pages are moved to external static files.
    'style-src': ("'self'", "'unsafe-inline'", 'cdn.jsdelivr.net', 'cdnjs.cloudflare.com'),
    'script-src': ("'self'", "'unsafe-inline'", 'cdn.jsdelivr.net', 'cdnjs.cloudflare.com'),
    'font-src': ("'self'", 'cdnjs.cloudflare.com'),
    'img-src': ("'self'", 'data:', 'blob:'),
}

# ==================== FILE UPLOAD ====================
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
FILE_UPLOAD_PERMISSIONS = 0o644
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ==================== PAGINATION ====================
PAGINATION_DEFAULT = 20

# ==================== AUTHENTICATION CONFIGURATION ====================
LOGIN_URL = 'login'  # URL name or path where users are redirected if login is required
LOGIN_REDIRECT_URL = 'dashboard'  # URL name or path to redirect after successful login
LOGOUT_REDIRECT_URL = 'home'  # URL name or path to redirect after logout

# ==================== ROLE-BASED ACCESS ====================
ROLES = {
    'ADMIN': 'admin',
    'STAFF': 'staff',
    'STUDENT': 'student',
}
