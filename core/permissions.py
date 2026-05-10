"""Role-based permissions for ERP workflows."""

from functools import wraps

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import Group
from django.shortcuts import redirect

ROLE_SUPER_ADMIN = "Super Admin"
ROLE_ADMIN = "Admin"
ROLE_COUNSELOR = "Counselor"
ROLE_ACCOUNTANT = "Accountant"
ROLE_ATTENDANCE_MANAGER = "Attendance Manager"

ERP_ROLES = [
    ROLE_SUPER_ADMIN,
    ROLE_ADMIN,
    ROLE_COUNSELOR,
    ROLE_ACCOUNTANT,
    ROLE_ATTENDANCE_MANAGER,
]


def ensure_role_groups():
    for role_name in ERP_ROLES:
        Group.objects.get_or_create(name=role_name)


def user_has_role(user, *roles):
    if not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=roles).exists()


def roles_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if user_has_role(request.user, *roles):
                return view_func(request, *args, **kwargs)
            messages.error(request, "You do not have permission to access this page.")
            return redirect("dashboard" if request.user.is_authenticated else "login")

        return wrapper

    return decorator


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return user_has_role(self.request.user, ROLE_SUPER_ADMIN, ROLE_ADMIN)

    def handle_no_permission(self):
        messages.error(self.request, "Admin access required.")
        return redirect("home")


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return user_has_role(
            self.request.user,
            ROLE_SUPER_ADMIN,
            ROLE_ADMIN,
            ROLE_COUNSELOR,
            ROLE_ACCOUNTANT,
            ROLE_ATTENDANCE_MANAGER,
        )

    def handle_no_permission(self):
        messages.error(self.request, "Staff access required.")
        return redirect("home")


class StudentRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated

    def handle_no_permission(self):
        messages.warning(self.request, "Please login to continue.")
        return redirect("admin:login")


class OwnerOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        obj = self.get_object()
        if hasattr(obj, "created_by"):
            return obj.created_by == self.request.user
        if hasattr(obj, "user"):
            return obj.user == self.request.user
        if hasattr(obj, "owner"):
            return obj.owner == self.request.user
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to access this resource.")
        return redirect("home")


class RoleRequiredMixin(UserPassesTestMixin):
    required_role = None

    def test_func(self):
        if not self.required_role:
            raise ValueError("required_role must be defined in view")
        required_roles = (
            self.required_role if isinstance(self.required_role, (list, tuple, set)) else [self.required_role]
        )
        return user_has_role(self.request.user, *required_roles)

    def handle_no_permission(self):
        messages.error(self.request, "Required role not assigned.")
        return redirect("home")


def admin_required(view_func):
    return roles_required(ROLE_SUPER_ADMIN, ROLE_ADMIN)(view_func)


def staff_required(view_func):
    return roles_required(
        ROLE_SUPER_ADMIN,
        ROLE_ADMIN,
        ROLE_COUNSELOR,
        ROLE_ACCOUNTANT,
        ROLE_ATTENDANCE_MANAGER,
    )(view_func)


def student_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please login to continue.")
            return redirect("admin:login")
        return view_func(request, *args, **kwargs)

    return wrapper


def role_required(required_role):
    required_roles = required_role if isinstance(required_role, (list, tuple, set)) else [required_role]
    return roles_required(*required_roles)
