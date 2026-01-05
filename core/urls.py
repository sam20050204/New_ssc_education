from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Enquiry URLs
    path('enquiry/', views.enquiry_list, name='enquiry_list'),
    path('enquiry/<int:id>/', views.enquiry_detail, name='enquiry_detail'),
    path('enquiry/<int:id>/convert/', views.convert_enquiry_to_admission, name='convert_enquiry'),
    path('enquiry/<int:id>/delete/', views.delete_enquiry, name='delete_enquiry'),
    path('enquiry/export/', views.export_enquiries, name='export_enquiries'),
    
    # Admission URLs
    path('admission/', views.new_admission, name='new_admission'),
    path('admission/list/', views.admitted_students, name='admitted_students'),
    path('admission/<int:student_id>/detail/', views.student_detail_admitted, name='student_detail_admitted'),
    path('admission/<int:student_id>/update/', views.update_student_admitted, name='update_student_admitted'),
    path('admission/delete/', views.delete_admitted_students, name='delete_admitted_students'),
    
    # Fees Payment URLs - ✅ FIXED: Correct paths
    path('fees/payment/', views.fees_payment, name='fees_payment'),
    path('fees/search-students/', views.search_students_for_payment, name='search_students_for_payment'),
    path('fees/submit-payment/', views.submit_fee_payment, name='submit_fee_payment'),
    
    # Receipts URLs
    path('receipts/', views.receipts_view, name='receipts_view'),
    path('receipts/api/', views.get_receipts, name='get_receipts'),
    path('receipts/<int:receipt_id>/update/', views.update_receipt, name='update_receipt'),
    path('receipts/<int:receipt_id>/delete/', views.delete_receipt, name='delete_receipt'),
    path('receipts/export/', views.export_receipts, name='export_receipts'),
    
    # Export Functions
    path('export/students/', views.export_students_excel, name='export_students_excel'),
    path('export/admitted-students/', views.export_admitted_students_excel, name='export_admitted_students_excel'),
    
    # Courses
    path('add-course/', views.add_course_ajax, name='add_course_ajax'),
    
    # Database Management
    path('backup/database/', views.backup_database, name='backup_database'),
]