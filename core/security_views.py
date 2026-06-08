from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from core.audit_logs import get_client_ip, log_audit_event
from core.models import LoginAttempt
from core.permissions import ensure_role_groups


def _throttle_cache_key(username, ip_address):
    return f"login-throttle:{username.lower()}:{ip_address}"


@csrf_protect
@require_http_methods(["GET", "POST"])
def custom_login(request):
    ensure_role_groups()
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""
        ip_address = get_client_ip(request)
        cache_key = _throttle_cache_key(username or "anonymous", ip_address or "unknown")
        failure_limit = getattr(settings, "LOGIN_FAILURE_LIMIT", 5)
        failure_window = getattr(settings, "LOGIN_FAILURE_WINDOW", 900)
        failures = cache.get(cache_key, 0)

        if failures >= failure_limit:
            messages.error(request, "Too many failed login attempts. Please try again later.")
            LoginAttempt.objects.create(username=username, ip_address=ip_address, successful=False)
            return render(request, "core/login.html", status=429)

        user = authenticate(request, username=username, password=password)
        if user is None:
            cache.set(cache_key, failures + 1, failure_window)
            LoginAttempt.objects.create(username=username, ip_address=ip_address, successful=False)
            messages.error(request, "Invalid username or password.")
            return render(request, "core/login.html", status=401)

        cache.delete(cache_key)
        auth_login(request, user)
        LoginAttempt.objects.create(username=username, ip_address=ip_address, successful=True, user=user)
        log_audit_event(action="auth.login", actor=user, request=request, metadata={"username": username})
        next_url = request.GET.get("next", "dashboard")
        if not url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            next_url = "dashboard"
        return redirect(next_url)

    return render(request, "core/login.html")


@require_http_methods(["POST"])
def custom_logout(request):
    if request.user.is_authenticated:
        log_audit_event(action="auth.logout", actor=request.user, request=request)
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("home")
