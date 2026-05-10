from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views
from core import security_views

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),

    path('login/', security_views.custom_login, name='login'),

    path('logout/', security_views.custom_logout, name='logout'),

    path('', include('core.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Include django-debug-toolbar (if installed)
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except (ImportError, RuntimeError):
        pass
