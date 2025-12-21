from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
import csv

from .models import Enquiry


# ================= CUSTOM LOGOUT =================
def custom_logout(request):
    logout(request)
    messages.success(request, "You have been logged out successfully!")
    return redirect('home')


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
    from django.db.models.functions import ExtractYear
    
    # Get selected year from query parameter
    selected_year = request.GET.get('year', '')
    
    # Get all available years from enquiries
    available_years = (
        Enquiry.objects
        .annotate(year=ExtractYear('created_at'))
        .values_list('year', flat=True)
        .distinct()
        .order_by('-year')
    )
    
    # Filter enquiries based on selected year
    enquiries = Enquiry.objects.all()
    
    if selected_year:
        enquiries = enquiries.filter(created_at__year=selected_year)
    
    # Count total enquiries
    enquiry_count = enquiries.count()
    
    # Count by course (you can customize these filters based on your course names)
    mscit_count = enquiries.filter(course__icontains='MSCIT').count()
    klic_count = enquiries.filter(course__icontains='KLIC').count()
    
    return render(request, "core/dashboard.html", {
        "enquiry_count": enquiry_count,
        "mscit_count": mscit_count,
        "klic_count": klic_count,
        "available_years": available_years,
        "selected_year": selected_year,
        "active_page": "dashboard"
    })


# ================= ENQUIRY LIST =================
@login_required
def enquiry_list(request):
    from django.db.models.functions import ExtractYear
    
    # Get filter parameters
    search = request.GET.get("search", "")
    month = request.GET.get("month", "")
    year = request.GET.get("year", "")
    course = request.GET.get("course", "")
    
    # Start with all enquiries, ordered by latest first
    enquiries = Enquiry.objects.all().order_by("-created_at")
    
    # Apply filters
    if search:
        enquiries = enquiries.filter(
            Q(name__icontains=search) |
            Q(mobile__icontains=search) |
            Q(course__icontains=search)
        )
    
    if month:
        enquiries = enquiries.filter(created_at__month=month)
    
    if year:
        enquiries = enquiries.filter(created_at__year=year)
    
    if course:
        enquiries = enquiries.filter(course=course)
    
    # Get available years for filter dropdown
    available_years = (
        Enquiry.objects
        .annotate(year=ExtractYear('created_at'))
        .values_list('year', flat=True)
        .distinct()
        .order_by('-year')
    )
    
    # Get available courses for filter dropdown
    available_courses = (
        Enquiry.objects
        .values_list('course', flat=True)
        .distinct()
        .order_by('course')
    )
    
    # Pagination
    paginator = Paginator(enquiries, 10)  # 10 per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    # Build filter query string for pagination links
    filters_query = ""
    if search:
        filters_query += f"&search={search}"
    if month:
        filters_query += f"&month={month}"
    if year:
        filters_query += f"&year={year}"
    if course:
        filters_query += f"&course={course}"
    
    return render(request, "core/enquiries.html", {
        "page_obj": page_obj,
        "search": search,
        "month": month,
        "year": year,
        "course": course,
        "available_years": available_years,
        "available_courses": available_courses,
        "filters_query": filters_query,
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
    from django.utils import timezone
    
    # Get filter parameters
    search = request.GET.get("search", "")
    month = request.GET.get("month", "")
    year = request.GET.get("year", "")
    course = request.GET.get("course", "")
    
    # Start with all enquiries, ordered by latest first
    enquiries = Enquiry.objects.all().order_by("-created_at")
    
    # Apply same filters as list view
    if search:
        enquiries = enquiries.filter(
            Q(name__icontains=search) |
            Q(mobile__icontains=search) |
            Q(course__icontains=search)
        )
    
    if month:
        enquiries = enquiries.filter(created_at__month=month)
    
    if year:
        enquiries = enquiries.filter(created_at__year=year)
    
    if course:
        enquiries = enquiries.filter(course=course)
    
    # Create CSV response
    response = HttpResponse(content_type="text/csv")
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    response["Content-Disposition"] = f'attachment; filename="enquiries_{timestamp}.csv"'

    writer = csv.writer(response)
    writer.writerow(["ID", "Name", "Mobile", "Education", "Course", "Date & Time"])

    for e in enquiries:
        writer.writerow([
            e.id,
            e.name,
            e.mobile,
            e.education,
            e.course,
            e.created_at.strftime("%d-%m-%Y %I:%M %p")
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


# ================= NEW ADMISSION =================
@login_required
def new_admission(request):
    from .models import AdmittedStudent
    
    if request.method == "POST":
        try:
            # Get form data
            course = request.POST.get("course")
            custom_course = request.POST.get("custom_course", "")
            student_name = request.POST.get("student_name")
            father_name = request.POST.get("father_name")
            surname = request.POST.get("surname")
            mother_name = request.POST.get("mother_name")
            full_name = request.POST.get("full_name")
            date_of_birth = request.POST.get("date_of_birth")
            mobile_own = request.POST.get("mobile_own")
            parent_mobile = request.POST.get("parent_mobile", "")
            gender = request.POST.get("gender")
            marital_status = request.POST.get("marital_status")
            address = request.POST.get("address")
            city = request.POST.get("city")
            tehsil_block = request.POST.get("tehsil_block")
            district = request.POST.get("district")
            pin_code = request.POST.get("pin_code")
            educational_qualification = request.POST.get("educational_qualification")
            photo = request.FILES.get("photo")
            
            # Create admission record
            admission = AdmittedStudent.objects.create(
                course=course,
                custom_course=custom_course if course == "Other" else "",
                student_name=student_name,
                father_name=father_name,
                surname=surname,
                mother_name=mother_name,
                full_name=full_name,
                date_of_birth=date_of_birth,
                mobile_own=mobile_own,
                parent_mobile=parent_mobile,
                gender=gender,
                marital_status=marital_status,
                address=address,
                city=city,
                tehsil_block=tehsil_block,
                district=district,
                pin_code=pin_code,
                educational_qualification=educational_qualification,
                photo=photo
            )
            
            messages.success(request, f"Admission for {full_name} has been successfully recorded!")
            return redirect("new_admission")
            
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
    
    return render(request, "core/new_admission.html", {
        "active_page": "admission"
    })


# ================= ADMITTED STUDENTS LIST =================
@login_required
def admitted_students(request):
    from .models import AdmittedStudent
    
    students = AdmittedStudent.objects.all().order_by('-admission_date')
    
    return render(request, "core/admitted_students.html", {
        "students": students,
        "active_page": "admission"
    })

