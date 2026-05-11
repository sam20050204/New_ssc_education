from django.urls import path

from admissions import views as admission_views
from attendance import views as attendance_views
from batch_management import views as batch_views
from finance import views as finance_views
from reports import views as report_views

from . import views

urlpatterns = [
    # Home & Auth
    path("", views.home, name="home"),
    path("logout/", views.custom_logout, name="logout"),
    # Dashboard
    path("dashboard/", views.dashboard, name="dashboard"),
    path("education/", views.education_home, name="education_home"),
    path("admission-pipeline/", views.admission_pipeline_dashboard, name="admission_pipeline"),
    path("notifications/", views.notifications_page, name="notifications_page"),
    path("communications/", views.communications_page, name="communications_page"),
    # Enquiry URLs
    path("enquiry/", views.enquiry_list, name="enquiry_list"),
    path("enquiry/<int:id>/", views.enquiry_detail, name="enquiry_detail"),
    path("enquiry/<int:id>/convert/", views.convert_enquiry_to_admission, name="convert_enquiry"),
    path("enquiry/<int:id>/delete/", views.delete_enquiry, name="delete_enquiry"),
    path("enquiry/export/", views.export_enquiries, name="export_enquiries"),
    # Admission URLs
    path("admission/", admission_views.new_admission, name="new_admission"),
    path("admission/import/", views.import_admissions_excel, name="import_admissions_excel"),
    path("admission/import-photos/", views.import_student_photos_zip, name="import_photos"),
    path("admission/list/", views.admitted_students, name="admitted_students"),
    path("admission/search-students/", views.search_admitted_students, name="search_admitted_students"),
    path("admission/<int:student_id>/detail/", views.student_detail_admitted, name="student_detail_admitted"),
    path("admission/<int:student_id>/update/", views.update_student_admitted, name="update_student_admitted"),
    path("admission/delete/", views.delete_admitted_students, name="delete_admitted_students"),
    # Fees Payment URLs
    path("fees/payment/", finance_views.fees_payment, name="fees_payment"),
    path("fees/search-students/", finance_views.search_students_for_payment, name="search_students_for_payment"),
    path("fees/submit-payment/", finance_views.submit_fee_payment, name="submit_fee_payment"),
    # Receipts URLs
    path("receipts/", views.receipts_view, name="receipts_view"),
    path("receipts/api/", views.get_receipts, name="get_receipts"),
    path("receipts/<int:receipt_id>/update/", views.update_receipt, name="update_receipt"),  # ✅ ADD THIS
    path("receipts/<int:receipt_id>/delete/", views.delete_receipt, name="delete_receipt"),
    path("receipts/export/", views.export_receipts, name="export_receipts"),
    # Payment Tracking URLs
    path("payment-tracking/", views.payment_tracking, name="payment_tracking"),
    path(
        "payment-tracking/<int:student_id>/detail/",
        views.payment_tracking_student_detail,
        name="payment_tracking_student_detail",
    ),
    # Export Functions
    path("export/students/", views.export_students_excel, name="export_students_excel"),
    path("export/admitted-students/", views.export_admitted_students_excel, name="export_admitted_students_excel"),
    # Courses
    path("add-course/", views.add_course_ajax, name="add_course_ajax"),
    # Database Management / Backup
    path("backup/", views.backup_page, name="backup_page"),
    path("backup/export/", views.export_database, name="export_database"),
    path("backup/import/", views.import_database, name="import_database"),
    # Statistics URLs
    path("statistics/", views.statistics_view, name="statistics"),
    path("student-finance-details/", views.student_finance_details, name="student_finance_details"),
    path("update-finance-detail/", views.update_finance_detail, name="update_finance_detail"),
    path("month-wise-admission/", views.month_wise_admission, name="month_wise_admission"),
    # Sales and Services URLs
    path("sales/", views.sales_services_dashboard, name="sales_services_dashboard"),
    path("sales/items/", views.sales_items, name="sales_items"),
    path("sales/items/add/", views.add_sales_item, name="add_sales_item"),
    # Timetable & Attendance Management URLs
    path("timetable/", views.student_timetable, name="student_timetable"),
    path("timetable/<int:student_id>/edit/", views.edit_student_batch, name="edit_student_batch"),
    path("batch/overview/", batch_views.batch_overview_dashboard, name="batch_overview"),
    path("batch/active/", batch_views.active_batches, name="active_batches"),
    path("batch/end/", batch_views.end_batch, name="end_batch"),
    path("batch/end/confirm/", batch_views.end_batch_confirm, name="end_batch_confirm"),
    path("batch/ended/", batch_views.ended_batches, name="ended_batches"),
    path("batch/restore/", batch_views.restore_batch, name="restore_batch"),
    path("batch/restore/confirm/", batch_views.restore_batch_confirm, name="restore_batch_confirm"),
    path("batch/reports/", batch_views.batch_reports, name="batch_reports"),
    path("batch/reports/export/", batch_views.export_batch_reports, name="export_batch_reports"),
    path("batch/create/", batch_views.create_batch_view, name="create_batch"),
    path("batch/<int:batch_id>/delete/", batch_views.delete_batch, name="delete_batch"),
    path("batch/<int:batch_id>/edit/", views.edit_batch, name="edit_batch"),
    path("batch/list/", views.get_batch_list, name="get_batch_list"),
    path("batch/get-id/", views.get_batch_id, name="get_batch_id"),
    path("batch/students/", views.get_batch_students, name="get_batch_students"),
    path("batch/students/update/", views.update_batch_students, name="update_batch_students"),
    path("batch/update-capacity/", views.update_batch_capacity, name="update_batch_capacity"),
    path("admission/all/", views.get_all_students, name="get_all_students"),
    path("admission/<int:student_id>/batch-detail/", views.get_student_detail_batch, name="get_student_detail_batch"),
    path("attendance/mark/", attendance_views.mark_attendance_page, name="mark_attendance"),
    path(
        "attendance/save/<str:date>/<str:batch_time>/<str:batch_type>/",
        attendance_views.save_attendance,
        name="save_attendance",
    ),
    path("attendance/reports/", attendance_views.attendance_reports, name="attendance_reports"),
    path("export/timetable/", views.export_timetable_excel, name="export_timetable"),
    path("export/attendance/", views.export_attendance_report_excel, name="export_attendance_report"),
    path("health/", report_views.healthcheck, name="healthcheck"),
    path("api/notifications/", views.notifications_feed_api, name="notifications_feed_api"),
    path("api/notifications/settings/", views.notification_settings_api, name="notification_settings_api"),
    path("api/notifications/mark-all-read/", views.notification_mark_all_read, name="notification_mark_all_read"),
    path("api/notifications/<int:notification_id>/read/", views.notification_mark_read, name="notification_mark_read"),
    path("api/communications/threads/", views.communication_threads_api, name="communication_threads_api"),
    path("api/communications/threads/create/", views.communication_thread_create, name="communication_thread_create"),
    path(
        "api/communications/threads/<int:thread_id>/",
        views.communication_thread_detail,
        name="communication_thread_detail",
    ),
    path(
        "api/communications/threads/<int:thread_id>/comment/",
        views.communication_thread_comment,
        name="communication_thread_comment",
    ),
    path(
        "api/communications/threads/<int:thread_id>/read/",
        views.communication_thread_mark_read,
        name="communication_thread_mark_read",
    ),
]
