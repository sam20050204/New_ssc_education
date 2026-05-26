from django.contrib import admin

from .admin_customization import (
    AdmittedStudentAdmin,
    CourseAdmin,
    CustomAdminSite,
    EnquiryAdmin,
    FeePaymentAdmin,
    StudentAdmin,
    StudentFinanceDetailAdmin,
)
from .models import (
    AdmittedStudent,
    Attendance,
    AuditLog,
    Batch,
    BatchActionLog,
    Course,
    Enquiry,
    FeePayment,
    LoginAttempt,
    Student,
    StudentFinanceDetail,
)

# Register custom admin site
admin.site.__class__ = CustomAdminSite
admin.site.site_header = "SSC Education Administration"
admin.site.site_title = "SSC Education Admin"
admin.site.index_title = "Welcome to SSC Education Management System"

# Register all models with enhanced admin classes
admin.site.register(Enquiry, EnquiryAdmin)
admin.site.register(AdmittedStudent, AdmittedStudentAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(FeePayment, FeePaymentAdmin)
admin.site.register(StudentFinanceDetail, StudentFinanceDetailAdmin)


class AttendanceAdmin(admin.ModelAdmin):
    """Admin interface for Student Attendance Records"""

    list_display = ["student", "date", "theory_status", "practical_status", "marked_by", "created_at"]
    list_filter = ["date", "theory_attendance", "practical_attendance", "created_at"]
    search_fields = ["student__full_name", "student__student_name", "student__mobile_own"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["student", "marked_by"]

    fieldsets = (
        ("Student Information", {"fields": ("student", "date")}),
        ("Attendance Details", {"fields": ("theory_attendance", "practical_attendance", "remarks")}),
        ("Tracking Information", {"fields": ("marked_by", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def theory_status(self, obj):
        """Display theory attendance status with color"""
        return obj.get_theory_attendance_display()

    theory_status.short_description = "Theory"

    def practical_status(self, obj):
        """Display practical attendance status with color"""
        return obj.get_practical_attendance_display()

    practical_status.short_description = "Practical"

    def save_model(self, request, obj, form, change):
        """Auto-fill marked_by with current user"""
        if not obj.marked_by:
            obj.marked_by = request.user
        super().save_model(request, obj, form, change)


class BatchAdmin(admin.ModelAdmin):
    """Admin interface for Batch Management"""

    list_display = ["batch_type", "time_slot", "course", "capacity", "current_strength"]
    list_filter = ["batch_type", "time_slot", "course"]
    search_fields = ["course__name"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Batch Information", {"fields": ("batch_type", "time_slot", "course")}),
        ("Capacity", {"fields": ("capacity",)}),
        ("Metadata", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


admin.site.register(Attendance, AttendanceAdmin)
admin.site.register(Batch, BatchAdmin)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["created_at", "action", "actor", "target_repr", "ip_address"]
    list_filter = ["action", "created_at"]
    search_fields = ["action", "target_repr", "actor__username", "object_id"]
    readonly_fields = [
        "created_at",
        "action",
        "actor",
        "content_type",
        "object_id",
        "target_repr",
        "metadata",
        "ip_address",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ["created_at", "username", "successful", "ip_address", "user"]
    list_filter = ["successful", "created_at"]
    search_fields = ["username", "ip_address", "user__username"]
    readonly_fields = ["created_at", "username", "successful", "ip_address", "user"]

    def has_add_permission(self, request):
        return False


@admin.register(BatchActionLog)
class BatchActionLogAdmin(admin.ModelAdmin):
    list_display = ["batch_month", "batch_year", "action_type", "action_by", "action_date", "affected_students_count"]
    list_filter = ["action_type", "batch_year", "action_date"]
    search_fields = ["batch_month", "batch_year", "remarks", "action_by__username"]
    readonly_fields = [
        "batch_month",
        "batch_year",
        "action_type",
        "action_by",
        "action_date",
        "affected_students_count",
        "remarks",
    ]

    def has_add_permission(self, request):
        return False
