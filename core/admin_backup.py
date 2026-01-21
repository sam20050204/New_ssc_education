from django.contrib import admin
from .models import Enquiry, AdmittedStudent, Course, Student, FeePayment, StudentFinanceDetail


@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ("name", "mobile", "course")
    search_fields = ("name", "mobile")
    list_filter = ("course",)


@admin.register(AdmittedStudent)
class AdmittedStudentAdmin(admin.ModelAdmin):
    list_display = ("full_name", "course", "mobile_own", "city")
    search_fields = ("full_name", "mobile_own")
    list_filter = ("course",)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "duration")
    search_fields = ("name",)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("name", "course", "phone", "is_active")
    search_fields = ("name", "phone")
    list_filter = ("is_active", "course")


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ("receipt_no", "student", "amount", "payment_mode")
    search_fields = ("receipt_no", "student__full_name")
    list_filter = ("payment_mode",)
    readonly_fields = ("receipt_no", "payment_date", "created_at", "updated_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(StudentFinanceDetail)
class StudentFinanceDetailAdmin(admin.ModelAdmin):
    list_display = ("student",)
    search_fields = ("student__full_name",)
    readonly_fields = ("created_at", "updated_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
