import logging
import time
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import logout
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("core")


class LoggingMiddleware(MiddlewareMixin):
    """Log all HTTP requests and responses with timing information"""

    def process_request(self, request):
        """Log incoming request"""
        request.start_time = time.time()
        user = request.user.username if request.user.is_authenticated else "Anonymous"
        logger.info(f"-> {request.method} {request.path} | User: {user} | IP: {self.get_client_ip(request)}")
        return None

    def process_response(self, request, response):
        """Log outgoing response with timing"""
        duration = time.time() - request.start_time if hasattr(request, "start_time") else 0
        user = request.user.username if request.user.is_authenticated else "Anonymous"
        status = response.status_code

        logger.info(f"<- {status} {request.method} {request.path} | Time: {duration:.3f}s | User: {user}")

        if status >= 400:
            logger.error(
                f"ERROR: {status} {request.method} {request.path} | Referrer: {request.META.get('HTTP_REFERER', 'N/A')}"
            )

        return response

    @staticmethod
    def get_client_ip(request):
        """Get real client IP address (handles proxies)"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip





class SessionTimeoutMiddleware(MiddlewareMixin):
    """Expire idle authenticated sessions."""

    def process_request(self, request):
        if not getattr(request, "user", None) or not request.user.is_authenticated:
            return None

        if request.path.startswith("/static/") or request.path.startswith("/media/"):
            return None

        timeout_seconds = getattr(settings, "SESSION_IDLE_TIMEOUT", 1800)
        now = int(time.time())
        last_activity = request.session.get("last_activity")

        if last_activity and now - last_activity > timeout_seconds:
            logout(request)
            request.session.flush()
            return None

        request.session["last_activity"] = now
        return None
