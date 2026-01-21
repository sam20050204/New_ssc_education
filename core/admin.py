from django.contrib import admin
from .models import Enquiry, AdmittedStudent, Course, Student, FeePayment, StudentFinanceDetail


class BasicAdmin(admin.ModelAdmin):
    """Minimal admin configuration to avoid template rendering issues"""
    pass


@admin.register(Enquiry)
class EnquiryAdmin(BasicAdmin):
    pass


@admin.register(AdmittedStudent)
class AdmittedStudentAdmin(BasicAdmin):
    pass


@admin.register(Course)
class CourseAdmin(BasicAdmin):
    pass


@admin.register(Student)
class StudentAdmin(BasicAdmin):
    pass


@admin.register(FeePayment)
class FeePaymentAdmin(BasicAdmin):
    pass


@admin.register(StudentFinanceDetail)
class StudentFinanceDetailAdmin(BasicAdmin):
    pass
