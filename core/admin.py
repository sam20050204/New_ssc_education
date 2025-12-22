from django.contrib import admin
from .models import Enquiry, AdmittedStudent, Course, Student, FeePayment

@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ("name", "mobile", "education", "course", "created_at")
    search_fields = ("name", "mobile", "course")
    list_filter = ("course", "created_at")


@admin.register(AdmittedStudent)
class AdmittedStudentAdmin(admin.ModelAdmin):
    list_display = ("full_name", "course", "mobile_own", "city", "admission_date", "remaining_fees")
    search_fields = ("full_name", "student_name", "mobile_own", "city")
    list_filter = ("course", "gender", "marital_status", "admission_date")
    readonly_fields = ("admission_date", "updated_at", "remaining_fees", "fees_percentage_paid")
    
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
        ('Financial Information', {
            'fields': ('total_fees', 'paid_fees', 'remaining_fees', 'fees_percentage_paid')
        }),
        ('Metadata', {
            'fields': ('admission_date', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "duration")
    search_fields = ("name",)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("name", "course", "phone", "admission_date", "remaining_fees", "is_active")
    search_fields = ("name", "phone", "email")
    list_filter = ("course", "is_active", "admission_date")
    readonly_fields = ("created_at", "updated_at", "remaining_fees", "fees_percentage_paid")
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'phone', 'email', 'photo', 'date_of_birth', 'qualification')
        }),
        ('Course Information', {
            'fields': ('course', 'admission_date')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'pincode')
        }),
        ('Parent/Guardian', {
            'fields': ('parent_name', 'parent_phone')
        }),
        ('Financial', {
            'fields': ('total_fees', 'paid_fees', 'remaining_fees', 'fees_percentage_paid')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ("receipt_no", "student", "amount", "payment_mode", "payment_date", "remaining_after_this")
    search_fields = ("receipt_no", "student__full_name", "student__mobile_own")
    list_filter = ("payment_mode", "payment_date")
    readonly_fields = ("receipt_no", "payment_date", "created_at", "updated_at")
    
    fieldsets = (
        ('Receipt Information', {
            'fields': ('receipt_no', 'payment_date')
        }),
        ('Student Information', {
            'fields': ('student',)
        }),
        ('Payment Details', {
            'fields': ('amount', 'payment_mode', 'remarks')
        }),
        ('Fees Snapshot', {
            'fields': ('total_fees_at_payment', 'paid_before_this', 'remaining_after_this'),
            'description': 'Snapshot of fees at the time of payment'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Disable adding payments directly from admin
        # Payments should be added through the fees payment page
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Disable deleting payments
        # This is to maintain financial integrity
        return False