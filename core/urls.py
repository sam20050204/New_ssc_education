from django.urls import path
from . import views

urlpatterns = [
    # Home & Auth
    path('', views.home, name='home'),
    path('logout/', views.custom_logout, name='logout'),
    
    # Dashboard
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
    path('admission/search-students/', views.search_admitted_students, name='search_admitted_students'),
    path('admission/<int:student_id>/detail/', views.student_detail_admitted, name='student_detail_admitted'),
    path('admission/<int:student_id>/update/', views.update_student_admitted, name='update_student_admitted'),
    path('admission/delete/', views.delete_admitted_students, name='delete_admitted_students'),
    
    # Fees Payment URLs
    path('fees/payment/', views.fees_payment, name='fees_payment'),
    path('fees/search-students/', views.search_students_for_payment, name='search_students_for_payment'),
    path('fees/submit-payment/', views.submit_fee_payment, name='submit_fee_payment'),
    
    # Receipts URLs
    path('receipts/', views.receipts_view, name='receipts_view'),
    path('receipts/api/', views.get_receipts, name='get_receipts'),
    path('receipts/<int:receipt_id>/update/', views.update_receipt, name='update_receipt'),  # ✅ ADD THIS
    path('receipts/<int:receipt_id>/delete/', views.delete_receipt, name='delete_receipt'),
    path('receipts/export/', views.export_receipts, name='export_receipts'),
    
    # Payment Tracking URLs
    path('payment-tracking/', views.payment_tracking, name='payment_tracking'),
    path('payment-tracking/<int:student_id>/detail/', views.payment_tracking_student_detail, name='payment_tracking_student_detail'),
    
    # Export Functions
    path('export/students/', views.export_students_excel, name='export_students_excel'),
    path('export/admitted-students/', views.export_admitted_students_excel, name='export_admitted_students_excel'),
    
    # Courses
    path('add-course/', views.add_course_ajax, name='add_course_ajax'),
    
    # Database Management / Backup
    path('backup/', views.backup_page, name='backup_page'),
    path('backup/export/', views.export_database, name='export_database'),
    path('backup/import/', views.import_database, name='import_database'),
    
    #Statistics URLs
    path('statistics/', views.statistics_view, name='statistics'),
    
    path('student-finance-details/', views.student_finance_details, name='student_finance_details'),
    path('update-finance-detail/', views.update_finance_detail, name='update_finance_detail'),
    path('month-wise-admission/', views.month_wise_admission, name='month_wise_admission'),
    
    # Sales and Services URLs
    path('sales/', views.sales_services_dashboard, name='sales_services_dashboard'),
    path('sales/items/', views.sales_items, name='sales_items'),
    path('sales/items/add/', views.add_sales_item, name='add_sales_item'),
    
    # Timetable & Attendance Management URLs
    path('timetable/', views.student_timetable, name='student_timetable'),
    path('timetable/<int:student_id>/edit/', views.edit_student_batch, name='edit_student_batch'),
    path('batch/overview/', views.batch_overview_dashboard, name='batch_overview'),
    path('batch/create/', views.create_batch, name='create_batch'),
    path('batch/<int:batch_id>/delete/', views.delete_batch, name='delete_batch'),
    path('batch/<int:batch_id>/edit/', views.edit_batch, name='edit_batch'),
    path('batch/list/', views.get_batch_list, name='get_batch_list'),
    path('batch/get-id/', views.get_batch_id, name='get_batch_id'),
    path('batch/students/', views.get_batch_students, name='get_batch_students'),
    path('batch/students/update/', views.update_batch_students, name='update_batch_students'),
    path('admission/all/', views.get_all_students, name='get_all_students'),
    path('admission/<int:student_id>/batch-detail/', views.get_student_detail_batch, name='get_student_detail_batch'),
    path('attendance/mark/', views.mark_attendance_page, name='mark_attendance'),
    path('attendance/save/<str:date>/<str:batch_time>/<str:batch_type>/', views.save_attendance, name='save_attendance'),
    path('attendance/reports/', views.attendance_reports, name='attendance_reports'),
    path('export/timetable/', views.export_timetable_excel, name='export_timetable'),
    path('export/attendance/', views.export_attendance_report_excel, name='export_attendance_report'),
]