from django.contrib import admin
from .models import Enquiry, AdmittedStudent, Course, Student, FeePayment, StudentFinanceDetail, SalesItem


@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'mobile', 'education', 'course', 'city', 'created_at')
    search_fields = ('name', 'mobile', 'course', 'city')
    list_filter = ('course', 'education', 'created_at')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


@admin.register(AdmittedStudent)
class AdmittedStudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'course', 'mobile_own', 'city', 'admission_date', 'paid_fees', 'total_fees')
    search_fields = ('full_name', 'mobile_own', 'student_name', 'city', 'district')
    list_filter = ('course', 'gender', 'city', 'admission_date')
    readonly_fields = ('admission_date', 'updated_at')
    fieldsets = (
        ('Personal Information', {
            'fields': ('student_name', 'father_name', 'mother_name', 'surname', 'full_name', 'date_of_birth')
        }),
        ('Contact Information', {
            'fields': ('mobile_own', 'parent_mobile')
        }),
        ('Demographics', {
            'fields': ('gender', 'marital_status')
        }),
        ('Course Information', {
            'fields': ('course', 'custom_course', 'batch_month', 'batch_year')
        }),
        ('Address', {
            'fields': ('address', 'city', 'tehsil_block', 'district', 'pin_code')
        }),
        ('Education', {
            'fields': ('educational_qualification',)
        }),
        ('Financial', {
            'fields': ('total_fees', 'paid_fees')
        }),
        ('Media & Metadata', {
            'fields': ('photo', 'admission_date', 'updated_at')
        }),
    )
    ordering = ('-admission_date',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'phone', 'city', 'is_active', 'created_at')
    search_fields = ('name', 'phone', 'email', 'city')
    list_filter = ('is_active', 'course', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ('receipt_no', 'student', 'amount', 'payment_mode', 'payment_date', 'created_at')
    search_fields = ('receipt_no', 'student__full_name', 'payment_mode')
    list_filter = ('payment_mode', 'payment_date', 'created_at')
    readonly_fields = ('receipt_no', 'created_at', 'updated_at')
    ordering = ('-payment_date',)


@admin.register(StudentFinanceDetail)
class StudentFinanceDetailAdmin(admin.ModelAdmin):
    list_display = ('student', 'first_installment', 'second_installment', 'total_mkcl_fees', 'profit')
    search_fields = ('student__full_name',)
    readonly_fields = ('created_at', 'updated_at', 'total_mkcl_fees', 'profit')
    fieldsets = (
        ('Student Information', {
            'fields': ('student',)
        }),
        ('Installments', {
            'fields': ('first_installment', 'second_installment', 'third_installment')
        }),
        ('MKCL Fees', {
            'fields': ('fees_paid_to_mkcl_1', 'fees_paid_to_mkcl_2', 'total_mkcl_fees')
        }),
        ('Financial Summary', {
            'fields': ('profit',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(SalesItem)
class SalesItemAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'quantity', 'purchase_rate', 'total_amount', 'purchased_from', 'created_at')
    search_fields = ('item_name', 'purchased_from')
    list_filter = ('created_at', 'purchased_from')
    readonly_fields = ('created_at', 'updated_at', 'calculated_total')
    ordering = ('-created_at',)