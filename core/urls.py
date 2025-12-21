from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('enquiries/', views.enquiry_list, name='enquiry_list'),
    path('enquiries/export/', views.export_enquiries, name='export_enquiries'),
    path('enquiries/delete/<int:id>/', views.delete_enquiry, name='delete_enquiry'),
    path('enquiries/convert/<int:id>/', views.convert_enquiry, name='convert_enquiry'),


    ]
