from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('enquiries/', views.enquiry_list, name='enquiry_list'),
    path('enquiries/export/', views.export_enquiries, name='export_enquiries'),
    path('enquiries/delete/<int:id>/', views.delete_enquiry, name='delete_enquiry'),
    path('enquiries/convert/<int:id>/', views.convert_enquiry, name='convert_enquiry'),
    
    # New Admission URLs
    path('admission/new/', views.new_admission, name='new_admission'),
    path('admission/students/', views.admitted_students, name='admitted_students'),
    path('admitted-students/', views.admitted_students, name='admitted_students'),
    path('student-detail/<int:student_id>/', views.student_detail, name='student_detail'),
    path('update-student/<int:student_id>/', views.update_student, name='update_student'),
    path('export-students/', views.export_students_excel, name='export_students'),

]