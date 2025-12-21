from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
import csv

from .models import Enquiry


# ================= HOME PAGE =================
def home(request):
    if request.method == "POST":
        name = request.POST.get("name")
        mobile = request.POST.get("mobile")
        education = request.POST.get("education")
        course = request.POST.get("course")

        Enquiry.objects.create(
            name=name,
            mobile=mobile,
            education=education,
            course=course
        )

        messages.success(request, "Enquiry submitted successfully!")
        return redirect("home")

    return render(request, "core/home.html")


# ================= DASHBOARD =================
@login_required
def dashboard(request):
    enquiry_count = Enquiry.objects.count()

    return render(request, "core/dashboard.html", {
        "enquiry_count": enquiry_count,
        "active_page": "dashboard"
    })


# ================= ENQUIRY LIST =================
@login_required
def enquiry_list(request):
    search = request.GET.get("search", "")
    enquiries = Enquiry.objects.all().order_by("-created_at")

    if search:
        enquiries = enquiries.filter(
            Q(name__icontains=search) |
            Q(mobile__icontains=search) |
            Q(course__icontains=search)
        )

    paginator = Paginator(enquiries, 10)  # 10 per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "core/enquiries.html", {
        "page_obj": page_obj,
        "search": search,
        "active_page": "enquiries"
    })


# ================= DELETE ENQUIRY =================
@login_required
def delete_enquiry(request, id):
    enquiry = get_object_or_404(Enquiry, id=id)
    enquiry.delete()
    messages.success(request, "Enquiry deleted successfully")
    return redirect("enquiry_list")


# ================= EXPORT ENQUIRIES =================
@login_required
def export_enquiries(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="enquiries.csv"'

    writer = csv.writer(response)
    writer.writerow(["ID", "Name", "Mobile", "Education", "Course", "Date"])

    enquiries = Enquiry.objects.all().order_by("-created_at")

    for e in enquiries:
        writer.writerow([
            e.id,
            e.name,
            e.mobile,
            e.education,
            e.course,
            e.created_at.strftime("%d-%m-%Y")
        ])

    return response


# ================= CONVERT ENQUIRY TO ADMISSION =================
@login_required
def convert_enquiry(request, id):
    enquiry = get_object_or_404(Enquiry, id=id)
    return render(request, "core/admission_form.html", {
        "enquiry": enquiry,
        "active_page": "enquiries"
    })
