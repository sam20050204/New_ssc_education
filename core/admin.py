from django.contrib import admin
from .models import Enquiry, AdmittedStudent, Course, Student, FeePayment, StudentFinanceDetail, SalesItem, Attendance, Batch
from .admin_customization import (
    CustomAdminSite,
    EnquiryAdmin,
    AdmittedStudentAdmin,
    CourseAdmin,
    StudentAdmin,
    FeePaymentAdmin,
    StudentFinanceDetailAdmin,
    SalesItemAdmin,
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
admin.site.register(SalesItem, SalesItemAdmin)


class AttendanceAdmin(admin.ModelAdmin):
    """Admin interface for Student Attendance Records"""
    
    list_display = ['student', 'date', 'theory_status', 'practical_status', 'marked_by', 'created_at']
    list_filter = ['date', 'theory_attendance', 'practical_attendance', 'created_at']
    search_fields = ['student__full_name', 'student__student_name', 'student__mobile_own']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['student', 'marked_by']
    
    fieldsets = (
        ('Student Information', {
            'fields': ('student', 'date')
        }),
        ('Attendance Details', {
            'fields': ('theory_attendance', 'practical_attendance', 'remarks')
        }),
        ('Tracking Information', {
            'fields': ('marked_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def theory_status(self, obj):
        """Display theory attendance status with color"""
        return obj.get_theory_attendance_display()
    theory_status.short_description = 'Theory'
    
    def practical_status(self, obj):
        """Display practical attendance status with color"""
        return obj.get_practical_attendance_display()
    practical_status.short_description = 'Practical'
    
    def save_model(self, request, obj, form, change):
        """Auto-fill marked_by with current user"""
        if not obj.marked_by:
            obj.marked_by = request.user
        super().save_model(request, obj, form, change)


class BatchAdmin(admin.ModelAdmin):
    """Admin interface for Batch Management"""
    
    list_display = ['batch_type', 'time_slot', 'course', 'capacity', 'current_strength']
    list_filter = ['batch_type', 'time_slot', 'course']
    search_fields = ['course__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Batch Information', {
            'fields': ('batch_type', 'time_slot', 'course')
        }),
        ('Capacity', {
            'fields': ('capacity',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


admin.site.register(Attendance, AttendanceAdmin)
admin.site.register(Batch, BatchAdmin)
