from django.contrib import admin
from .models import Enquiry, AdmittedStudent

@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ("name", "mobile", "education", "course", "created_at")
    search_fields = ("name", "mobile", "course")
    list_filter = ("course", "created_at")


@admin.register(AdmittedStudent)
class AdmittedStudentAdmin(admin.ModelAdmin):
    list_display = ("full_name", "course", "mobile_own", "city", "admission_date")
    search_fields = ("full_name", "student_name", "mobile_own", "city")
    list_filter = ("course", "gender", "marital_status", "admission_date")
    readonly_fields = ("admission_date", "updated_at")
    
    fieldsets = (
        ('Course Information', {
            'fields': ('course', 'custom_course')
        }),
        ('Personal Information', {
            'fields': ('student_name', 'father_name', 'surname', 'mother_name', 'full_name', 'date_of_birth')
        }),
        ('Contact Information', {
            'fields': ('mobile_own', 'parent_mobile')
        }),
        ('Demographics', {
            'fields': ('gender', 'marital_status')
        }),
        ('Address Information', {
            'fields': ('address', 'city', 'tehsil_block', 'district', 'pin_code')
        }),
        ('Educational Information', {
            'fields': ('educational_qualification',)
        }),
        ('Photo', {
            'fields': ('photo',)
        }),
        ('Metadata', {
            'fields': ('admission_date', 'updated_at'),
            'classes': ('collapse',)
        }),
    )