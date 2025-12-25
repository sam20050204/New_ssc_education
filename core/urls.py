from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('enquiries/', views.enquiry_list, name='enquiry_list'),
    path('enquiries/export/', views.export_enquiries, name='export_enquiries'),
    path('enquiries/delete/<int:id>/', views.delete_enquiry, name='delete_enquiry'),
    path('enquiries/convert/<int:id>/', views.convert_enquiry, name='convert_enquiry'),
    
    # Admission URLs
    path('admission/new/', views.new_admission, name='new_admission'),
    path('admission/students/', views.admitted_students, name='admitted_students'),
    
    # Student Detail and Update URLs
    path('student-detail-admitted/<int:student_id>/', views.student_detail_admitted, name='student_detail_admitted'),
    path('update-student-admitted/<int:student_id>/', views.update_student_admitted, name='update_student_admitted'),
    
    # Delete Admitted Students
    path('delete-admitted-students/', views.delete_admitted_students, name='delete_admitted_students'),
    
    # Fees Payment URLs
    path('fees-payment/', views.fees_payment, name='fees_payment'),
    path('fees-payment/search/', views.search_students_for_payment, name='search_students_for_payment'),
    path('fees-payment/submit/', views.submit_fee_payment, name='submit_fee_payment'),
    
    # Export Students
    path('export-students-excel/', views.export_students_excel, name='export_students_excel'),
    
    # NEW: Export Admitted Students
    path('export-admitted-students-excel/', views.export_admitted_students_excel, name='export_admitted_students_excel'),

    # Receipts URLs
    path('receipts/', views.receipts_view, name='receipts_view'),
    path('api/receipts/', views.get_receipts, name='get_receipts'),
    path('api/receipts/<int:receipt_id>/update/', views.update_receipt, name='update_receipt'),
    path('api/receipts/export/', views.export_receipts, name='export_receipts'),
    path('api/receipts/<int:receipt_id>/delete/', views.delete_receipt, name='delete_receipt'),
]