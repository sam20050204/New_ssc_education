"""
Context Processors - Pass global variables to templates
"""

from django.conf import settings

from core.models import Notification
from core.services.collaboration_service import (
    ensure_notification_settings,
    get_recent_threads_for_user,
    seed_operational_notifications,
)


def static_version(request):
    """
    Add static file version to all templates for cache busting.
    Usage in templates: {{ STATIC_VERSION }}
    """
    return {"STATIC_VERSION": getattr(settings, "STATIC_VERSION", "1.0.0")}


def collaboration_context(request):
    user = getattr(request, "user", None)
    if not getattr(user, "is_authenticated", False):
        return {
            "topbar_unread_notifications": 0,
            "topbar_unread_threads": 0,
            "topbar_recent_notifications": [],
            "topbar_recent_threads": [],
        }

    ensure_notification_settings(user)
    seed_operational_notifications()

    notifications = Notification.objects.filter(recipient=user).select_related("actor")[:6]
    unread_notifications = Notification.objects.filter(recipient=user, is_read=False).count()
    recent_threads = list(get_recent_threads_for_user(user, limit=6))

    unread_threads = 0
    for thread in recent_threads:
        state = next((item for item in thread.participant_states.all() if item.user_id == user.id), None)
        latest_entry = thread.entries.order_by("-created_at").first()
        if latest_entry and (
            state is None or state.last_read_at is None or latest_entry.created_at > state.last_read_at
        ):
            unread_threads += 1

    return {
        "topbar_unread_notifications": unread_notifications,
        "topbar_unread_threads": unread_threads,
        "topbar_recent_notifications": notifications,
        "topbar_recent_threads": recent_threads,
    }


def current_mode(request):
    """
    Add current mode (education or sales) to all templates.
    Defaults to 'education' mode unless on a sales/finance page.
    """
    path = request.path
    
    # Define all paths that should be in 'sales' mode
    sales_paths = [
        '/sales',          # Sales dashboard and items
        '/inventory',      # Inventory module
    ]
    
    # Check if current path matches any sales-related paths
    for sales_path in sales_paths:
        if path.startswith(sales_path):
            return {'current_mode': 'sales'}
    
    # Default to education mode (includes fees, payment-tracking, receipts)
    return {'current_mode': 'education'}
