"""
Role-Based Access Control (RBAC) Mixins
Restrict views based on user roles/permissions
"""

from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from django.http import HttpResponseForbidden


# ==================== ROLE DEFINITIONS ====================
ROLES = {
    'ADMIN': 'admin',
    'STAFF': 'staff',
    'STUDENT': 'student',
    'VIEWER': 'viewer',
}


# ==================== CUSTOM PERMISSION MIXINS ====================

class AdminRequiredMixin(UserPassesTestMixin):
    """
    Restrict view to admin users only.
    
    Usage:
        class MyAdminView(AdminRequiredMixin, ListView):
            model = MyModel
    """
    
    def test_func(self):
        """Check if user is admin"""
        return self.request.user.is_staff and self.request.user.is_superuser
    
    def handle_no_permission(self):
        """Redirect to login if not admin"""
        messages.error(self.request, "❌ Admin access required!")
        return redirect('home')


class StaffRequiredMixin(UserPassesTestMixin):
    """
    Restrict view to staff users (admin + staff).
    
    Usage:
        class MyStaffView(StaffRequiredMixin, ListView):
            model = MyModel
    """
    
    def test_func(self):
        """Check if user is staff"""
        return self.request.user.is_staff
    
    def handle_no_permission(self):
        """Redirect to login if not staff"""
        messages.error(self.request, "❌ Staff access required!")
        return redirect('home')


class StudentRequiredMixin(UserPassesTestMixin):
    """
    Restrict view to authenticated users (students).
    
    Usage:
        class MyStudentView(StudentRequiredMixin, ListView):
            model = MyModel
    """
    
    def test_func(self):
        """Check if user is authenticated"""
        return self.request.user.is_authenticated
    
    def handle_no_permission(self):
        """Redirect to login if not authenticated"""
        messages.warning(self.request, "⚠️ Please login to continue!")
        return redirect('admin:login')


class OwnerOnlyMixin(UserPassesTestMixin):
    """
    Restrict view to object owner only.
    Used for detail/update/delete views.
    
    Usage:
        class MyDetailView(OwnerOnlyMixin, DetailView):
            model = MyModel
    """
    
    def test_func(self):
        """Check if user is the object owner"""
        obj = self.get_object()
        
        # Check various ownership patterns
        if hasattr(obj, 'created_by'):
            return obj.created_by == self.request.user
        elif hasattr(obj, 'user'):
            return obj.user == self.request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == self.request.user
        
        # Default: only superusers can access
        return self.request.user.is_superuser
    
    def handle_no_permission(self):
        """Deny access if not owner"""
        messages.error(self.request, "❌ You don't have permission to access this resource!")
        return redirect('home')


class RoleRequiredMixin(UserPassesTestMixin):
    """
    Generic mixin to check for specific roles.
    Must define 'required_role' in view.
    
    Usage:
        class MyRoleView(RoleRequiredMixin, ListView):
            model = MyModel
            required_role = 'admin'  # or 'staff', 'student'
    """
    
    required_role = None
    
    def test_func(self):
        """Check if user has required role"""
        if not self.required_role:
            raise ValueError("required_role must be defined in view")
        
        role = self.required_role.lower()
        
        if role == 'admin':
            return self.request.user.is_superuser
        elif role == 'staff':
            return self.request.user.is_staff
        elif role == 'student':
            return self.request.user.is_authenticated
        else:
            return False
    
    def handle_no_permission(self):
        """Deny access with role not found"""
        messages.error(self.request, f"❌ {self.required_role.upper()} access required!")
        return redirect('home')


# ==================== DECORATOR-BASED PERMISSIONS ====================

def admin_required(view_func):
    """
    Decorator for function-based views - requires admin access.
    
    Usage:
        @admin_required
        def my_admin_view(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_staff and request.user.is_superuser):
            messages.error(request, "❌ Admin access required!")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


def staff_required(view_func):
    """
    Decorator for function-based views - requires staff access.
    
    Usage:
        @staff_required
        def my_staff_view(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, "❌ Staff access required!")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


def student_required(view_func):
    """
    Decorator for function-based views - requires student (authenticated) access.
    
    Usage:
        @student_required
        def my_student_view(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "⚠️ Please login to continue!")
            return redirect('admin:login')
        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(required_role):
    """
    Generic decorator for role-based access.
    
    Usage:
        @role_required('admin')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            role = required_role.lower()
            
            has_permission = False
            if role == 'admin':
                has_permission = request.user.is_superuser
            elif role == 'staff':
                has_permission = request.user.is_staff
            elif role == 'student':
                has_permission = request.user.is_authenticated
            
            if not has_permission:
                messages.error(request, f"❌ {required_role.upper()} access required!")
                return redirect('home')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# ==================== USAGE EXAMPLES ====================

"""
CLASS-BASED VIEWS:

from core.permissions import AdminRequiredMixin, StaffRequiredMixin
from django.views.generic import ListView

class AdminOnlyListView(AdminRequiredMixin, ListView):
    model = MyModel
    template_name = 'mytemplate.html'
    paginate_by = 20

class StaffListView(StaffRequiredMixin, ListView):
    model = MyModel


FUNCTION-BASED VIEWS:

from core.permissions import admin_required, staff_required

@admin_required
def admin_dashboard(request):
    return render(request, 'dashboard.html')

@staff_required
def staff_report(request):
    return render(request, 'report.html')


IN URLS.PY:

from django.urls import path
from . import views
from core.permissions import AdminRequiredMixin

urlpatterns = [
    path('admin-only/', AdminRequiredMixin.as_view(template_name='admin.html'), name='admin_only'),
]


IN TEMPLATES:

{% if user.is_superuser %}
    <a href="/admin/">Admin Panel</a>
{% endif %}

{% if user.is_staff %}
    <a href="/staff/reports/">Staff Reports</a>
{% endif %}

{% if user.is_authenticated %}
    <a href="/dashboard/">Dashboard</a>
{% endif %}
"""
