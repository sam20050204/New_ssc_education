from django.contrib import admin
from .models import Enquiry

@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ("name", "mobile", "education", "course", "created_at")
    search_fields = ("name", "mobile", "course")
    list_filter = ("course", "created_at")
