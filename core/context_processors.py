"""
Context Processors - Pass global variables to templates
"""
from django.conf import settings


def static_version(request):
    """
    Add static file version to all templates for cache busting.
    Usage in templates: {{ STATIC_VERSION }}
    """
    return {
        'STATIC_VERSION': getattr(settings, 'STATIC_VERSION', '1.0.0')
    }
