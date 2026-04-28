"""
Custom Admin Configuration
Improves admin interface styling and functionality
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from decimal import Decimal
from .models import (
    Enquiry, AdmittedStudent, Student, Course,
    FeePayment, StudentFinanceDetail, SalesItem
)


# Custom Admin Site Configuration
class CustomAdminSite(admin.AdminSite):
    site_header = "SSC Education Management"
    site_title = "Admin Portal"
    index_title = "Welcome to Admin Dashboard"
    
    def index(self, request, extra_context=None):
        """Customize admin dashboard"""
        extra_context = extra_context or {}
        
        # Get statistics
        total_enquiries = Enquiry.objects.count()
        total_students = AdmittedStudent.objects.count()
        total_revenue = FeePayment.objects.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        total_fees_collected = AdmittedStudent.objects.aggregate(Sum('paid_fees'))['paid_fees__sum'] or Decimal('0')
        
        extra_context.update({
            'total_enquiries': total_enquiries,
            'total_students': total_students,
            'total_revenue': total_revenue,
            'total_fees_collected': total_fees_collected,
        })
        
        return super().index(request, extra_context)


# Register models with custom admin
admin_site = CustomAdminSite(name='custom_admin')


@admin.register(Enquiry, site=admin_site)
class EnquiryAdmin(admin.ModelAdmin):
    """Admin interface for Enquiry model"""
    list_display = ('name', 'mobile', 'course', 'city', 'created_at_formatted')
    list_filter = ('course', 'city', 'created_at')
    search_fields = ('name', 'mobile', 'course')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'mobile', 'education')
        }),
        ('Course Information', {
            'fields': ('course', 'custom_course')
        }),
        ('Address', {
            'fields': ('address', 'city', 'taluka', 'district')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%d-%m-%Y %H:%M")
    created_at_formatted.short_description = "Submitted On"


@admin.register(AdmittedStudent, site=admin_site)
class AdmittedStudentAdmin(admin.ModelAdmin):
    """Admin interface for AdmittedStudent model"""
    list_display = ('full_name', 'course_display', 'mobile_own', 'admission_date', 'fees_status')
    list_filter = ('course', 'admission_date', 'gender', 'marital_status')
    search_fields = ('full_name', 'mobile_own', 'father_name')
    readonly_fields = ('admission_date', 'updated_at', 'remaining_fees', 'fees_percentage_paid')
    
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
        ('Address', {
            'fields': ('address', 'city', 'tehsil_block', 'district', 'pin_code')
        }),
        ('Education & Batch', {
            'fields': ('course', 'custom_course', 'educational_qualification', 'batch_month', 'batch_year')
        }),
        ('Financial Information', {
            'fields': ('total_fees', 'paid_fees', 'remaining_fees', 'fees_percentage_paid')
        }),
        ('Photo', {
            'fields': ('photo',)
        }),
        ('Metadata', {
            'fields': ('admission_date', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def course_display(self, obj):
        custom = obj.custom_course if obj.course == 'Other' else obj.course
        return custom
    course_display.short_description = "Course"
    
    def fees_status(self, obj):
        percentage = obj.fees_percentage_paid
        if percentage >= 100:
            color = 'green'
            status = '✓ Paid'
        elif percentage >= 50:
            color = 'orange'
            status = '⚠ Partial'
        else:
            color = 'red'
            status = '✗ Pending'
        return format_html(
            '<span style="color: {};">{} ({}%)</span>',
            color,
            status,
            int(percentage)
        )
    fees_status.short_description = "Fees Status"


@admin.register(Student, site=admin_site)
class StudentAdmin(admin.ModelAdmin):
    """Admin interface for Student model"""
    list_display = ('name', 'phone', 'course_name', 'admission_date', 'is_active')
    list_filter = ('is_active', 'course', 'admission_date')
    search_fields = ('name', 'phone', 'email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'phone', 'email', 'photo')
        }),
        ('Course Information', {
            'fields': ('course', 'admission_date')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'pincode')
        }),
        ('Guardian Information', {
            'fields': ('parent_name', 'parent_phone')
        }),
        ('Financial Information', {
            'fields': ('total_fees', 'paid_fees')
        }),
        ('Additional Information', {
            'fields': ('qualification', 'date_of_birth', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def course_name(self, obj):
        return obj.course.name if obj.course else '-'
    course_name.short_description = "Course"


@admin.register(Course, site=admin_site)
class CourseAdmin(admin.ModelAdmin):
    """Admin interface for Course model"""
    list_display = ('name', 'duration', 'student_count')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    
    def student_count(self, obj):
        count = obj.enrolled_students.count()
        return format_html(
            '<span style="background-color: #e3f2fd; padding: 5px 10px; border-radius: 3px;">{}</span>',
            count
        )
    student_count.short_description = "Enrolled Students"


@admin.register(FeePayment, site=admin_site)
class FeePaymentAdmin(admin.ModelAdmin):
    """Admin interface for FeePayment model"""
    list_display = ('receipt_no', 'student_link', 'amount_formatted', 'payment_mode', 'payment_date')
    list_filter = ('payment_mode', 'payment_date')
    search_fields = ('receipt_no', 'student__full_name')
    readonly_fields = ('receipt_no', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Receipt Information', {
            'fields': ('receipt_no', 'student')
        }),
        ('Payment Details', {
            'fields': ('amount', 'payment_mode', 'payment_date', 'remarks')
        }),
        ('Fee Snapshot', {
            'fields': ('total_fees_at_payment', 'paid_before_this', 'remaining_after_this'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def student_link(self, obj):
        url = f"/admin/core/admittedstudent/{obj.student.id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.student.full_name)
    student_link.short_description = "Student"
    
    def amount_formatted(self, obj):
        return f"₹{obj.amount:,.2f}"
    amount_formatted.short_description = "Amount"


@admin.register(StudentFinanceDetail, site=admin_site)
class StudentFinanceDetailAdmin(admin.ModelAdmin):
    """Admin interface for StudentFinanceDetail model"""
    list_display = ('student_link', 'total_installments', 'total_mkcl_fees', 'profit_formatted')
    readonly_fields = ('created_at', 'updated_at', 'total_mkcl_fees', 'profit')
    
    fieldsets = (
        ('Student Information', {
            'fields': ('student',)
        }),
        ('Fees Paid By Learner', {
            'fields': (
                'first_installment', 'second_installment', 'third_installment',
                'fourth_installment', 'fifth_installment'
            ),
            'description': 'Automatically populated from FeePayment records'
        }),
        ('Fees Paid to MKCL', {
            'fields': (
                'fees_paid_to_mkcl_1', 'fees_paid_to_mkcl_2', 'fees_paid_to_mkcl_3'
            ),
            'description': 'Enter the MKCL fees paid in each installment. Default is 0.'
        }),
        ('Summary', {
            'fields': ('total_mkcl_fees', 'profit'),
            'description': 'Auto-calculated based on the installments above'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def student_link(self, obj):
        url = f"/admin/core/admittedstudent/{obj.student.id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.student.full_name)
    student_link.short_description = "Student"
    
    def total_installments(self, obj):
        total = (obj.first_installment or 0) + (obj.second_installment or 0) + (obj.third_installment or 0)
        return f"₹{total:,.2f}"
    total_installments.short_description = "Total Installments"
    
    def profit_formatted(self, obj):
        profit = obj.profit
        color = 'green' if profit >= 0 else 'red'
        return format_html(
            '<span style="color: {};">₹{:,.2f}</span>',
            color,
            profit
        )
    profit_formatted.short_description = "Profit"


@admin.register(SalesItem, site=admin_site)
class SalesItemAdmin(admin.ModelAdmin):
    """Admin interface for SalesItem model"""
    list_display = ('item_name', 'quantity', 'purchase_rate_formatted', 'total_amount_formatted', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('item_name', 'purchased_from')
    readonly_fields = ('created_at', 'updated_at')
    
    def purchase_rate_formatted(self, obj):
        return f"₹{obj.purchase_rate:,.2f}"
    purchase_rate_formatted.short_description = "Purchase Rate"
    
    def total_amount_formatted(self, obj):
        return f"₹{obj.total_amount:,.2f}"
    total_amount_formatted.short_description = "Total Amount"
