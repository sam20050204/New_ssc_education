from django.contrib import admin
from .models import Enquiry, AdmittedStudent, Course, Student, FeePayment, StudentFinanceDetail, SalesItem
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