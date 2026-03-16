from django.contrib import admin
from .models import Enquiry, AdmittedStudent, Course, Student, FeePayment, StudentFinanceDetail, SalesItem, StudentTimetable
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


class StudentTimetableAdmin(admin.ModelAdmin):
    """Admin interface for Student Timetable"""
    
    list_display = ['student', 'day', 'time_slot', 'session_type', 'batch_month', 'course']
    list_filter = ['day', 'session_type', 'batch_month', 'course']
    search_fields = ['student__full_name', 'student__student_name', 'batch_month']
    readonly_fields = ['created_at', 'updated_at', 'batch_month', 'batch_year', 'course']
    
    fieldsets = (
        ('Student Information', {
            'fields': ('student',)
        }),
        ('Timetable Details', {
            'fields': ('day', 'time_slot', 'session_type', 'notes')
        }),
        ('Auto-filled Information', {
            'fields': ('batch_month', 'batch_year', 'course'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Auto-fill batch and course from student"""
        if obj.student:
            obj.batch_month = obj.student.batch_month
            obj.batch_year = obj.student.batch_year
            obj.course = obj.student.course
        super().save_model(request, obj, form, change)


admin.site.register(StudentTimetable, StudentTimetableAdmin)