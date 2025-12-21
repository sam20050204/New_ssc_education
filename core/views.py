from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models.functions import ExtractYear
import csv
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from io import BytesIO
from datetime import datetime

from .models import Enquiry, AdmittedStudent, Course, Student


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
    
    # Count by course
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
    paginator = Paginator(enquiries, 10)
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
            total_fees = request.POST.get("total_fees", 5000)
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
            
            messages.success(request, f"Admission for {full_name} has been successfully recorded! Total Fees: ₹{total_fees}")
            return redirect("new_admission")
            
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
    
    return render(request, "core/new_admission.html", {
        "active_page": "new_admission"
    })


# ================= ADMITTED STUDENTS LIST =================
@login_required
def admitted_students(request):
    # Get filter parameters
    search = request.GET.get("search", "")
    month = request.GET.get("month", "")
    year = request.GET.get("year", "")
    course = request.GET.get("course", "")
    
    # Start with all admitted students, ordered by latest first
    students = AdmittedStudent.objects.all().order_by('-admission_date')
    
    # Apply filters
    if search:
        students = students.filter(
            Q(full_name__icontains=search) |
            Q(student_name__icontains=search) |
            Q(mobile_own__icontains=search)
        )
    
    if month:
        students = students.filter(admission_date__month=month)
    
    if year:
        students = students.filter(admission_date__year=year)
    
    if course:
        students = students.filter(course=course)
    
    # Get available years for filter dropdown
    available_years = (
        AdmittedStudent.objects
        .annotate(year=ExtractYear('admission_date'))
        .values_list('year', flat=True)
        .distinct()
        .order_by('-year')
    )
    
    return render(request, 'core/admitted_students.html', {
        'students': students,
        'search': search,
        'month': month,
        'year': year,
        'course': course,
        'available_years': available_years,
        'active_page': 'admitted_students'
    })


# ================= STUDENT DETAIL (ADMITTED) =================
@login_required
def student_detail_admitted(request, student_id):
    student = get_object_or_404(AdmittedStudent, id=student_id)
    
    data = {
        'id': student.id,
        'student_name': student.student_name,
        'father_name': student.father_name,
        'surname': student.surname,
        'mother_name': student.mother_name,
        'full_name': student.full_name,
        'date_of_birth': student.date_of_birth.strftime('%Y-%m-%d'),
        'mobile_own': student.mobile_own,
        'parent_mobile': student.parent_mobile or '',
        'gender': student.gender,
        'marital_status': student.marital_status,
        'photo': student.photo.url if student.photo else '',
        'course': student.course,
        'custom_course': student.custom_course or '',
        'educational_qualification': student.educational_qualification,
        'address': student.address,
        'city': student.city,
        'tehsil_block': student.tehsil_block,
        'district': student.district,
        'pin_code': student.pin_code,
        'total_fees': 5000,  # Default or get from somewhere
        'paid_fees': 0,  # Default or get from somewhere
    }
    
    return JsonResponse(data)


# ================= UPDATE STUDENT (ADMITTED) =================
@login_required
def update_student_admitted(request, student_id):
    if request.method == 'POST':
        student = get_object_or_404(AdmittedStudent, id=student_id)
        
        # Update fields
        student.student_name = request.POST.get('student_name')
        student.father_name = request.POST.get('father_name')
        student.surname = request.POST.get('surname')
        student.mother_name = request.POST.get('mother_name')
        student.full_name = request.POST.get('full_name')
        student.date_of_birth = request.POST.get('date_of_birth')
        student.mobile_own = request.POST.get('mobile_own')
        student.parent_mobile = request.POST.get('parent_mobile')
        student.gender = request.POST.get('gender')
        student.marital_status = request.POST.get('marital_status')
        student.course = request.POST.get('course')
        student.custom_course = request.POST.get('custom_course')
        student.educational_qualification = request.POST.get('educational_qualification')
        student.address = request.POST.get('address')
        student.city = request.POST.get('city')
        student.tehsil_block = request.POST.get('tehsil_block')
        student.district = request.POST.get('district')
        student.pin_code = request.POST.get('pin_code')
        
        # Handle photo upload
        if request.FILES.get('photo'):
            student.photo = request.FILES['photo']
        
        student.save()
        
        messages.success(request, 'Student details updated successfully!')
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})


# ================= STUDENT DETAIL =================
@login_required
def student_detail(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    
    data = {
        'id': student.id,
        'name': student.name,
        'phone': student.phone,
        'email': student.email or '',
        'photo': student.photo.url if student.photo else '',
        'course': student.course.name if student.course else '',
        'course_id': student.course.id if student.course else '',
        'admission_date': student.admission_date.strftime('%Y-%m-%d'),
        'address': student.address or '',
        'city': student.city or '',
        'state': student.state or '',
        'pincode': student.pincode or '',
        'parent_name': student.parent_name or '',
        'parent_phone': student.parent_phone or '',
        'total_fees': str(student.total_fees),
        'paid_fees': str(student.paid_fees),
        'remaining_fees': str(student.remaining_fees),
        'qualification': student.qualification or '',
        'date_of_birth': student.date_of_birth.strftime('%Y-%m-%d') if student.date_of_birth else '',
    }
    
    return JsonResponse(data)


# ================= UPDATE STUDENT =================
@login_required
def update_student(request, student_id):
    if request.method == 'POST':
        student = get_object_or_404(Student, id=student_id)
        
        # Update basic info
        student.name = request.POST.get('name')
        student.phone = request.POST.get('phone')
        student.email = request.POST.get('email')
        student.address = request.POST.get('address')
        student.city = request.POST.get('city')
        student.state = request.POST.get('state')
        student.pincode = request.POST.get('pincode')
        student.parent_name = request.POST.get('parent_name')
        student.parent_phone = request.POST.get('parent_phone')
        student.qualification = request.POST.get('qualification')
        
        # Update course
        course_id = request.POST.get('course')
        if course_id:
            student.course_id = course_id
        
        # Update dates
        admission_date = request.POST.get('admission_date')
        if admission_date:
            student.admission_date = admission_date
        
        date_of_birth = request.POST.get('date_of_birth')
        if date_of_birth:
            student.date_of_birth = date_of_birth
        
        # Update financial info
        student.total_fees = request.POST.get('total_fees', 0)
        student.paid_fees = request.POST.get('paid_fees', 0)
        
        # Handle photo upload
        if request.FILES.get('photo'):
            student.photo = request.FILES['photo']
        
        student.save()
        
        messages.success(request, 'Student details updated successfully!')
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})


# ================= EXPORT STUDENTS TO EXCEL =================
@login_required
def export_students_excel(request):
    students = Student.objects.filter(is_active=True)
    
    # Apply same filters as the main view
    month = request.GET.get('month', '')
    year = request.GET.get('year', '')
    course_id = request.GET.get('course', '')
    
    if month and year:
        students = students.filter(
            admission_date__month=month,
            admission_date__year=year
        )
    elif year:
        students = students.filter(admission_date__year=year)
    
    if course_id:
        students = students.filter(course_id=course_id)
    
    students = students.order_by('admission_date', 'name')
    
    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Admitted Students"
    
    # Define headers
    headers = [
        'S.No', 'Name', 'Phone', 'Email', 'Course', 'Admission Date',
        'Address', 'City', 'State', 'Pincode', 'Parent Name', 'Parent Phone',
        'Qualification', 'Date of Birth', 'Total Fees', 'Paid Fees', 'Remaining Fees'
    ]
    
    # Style for header
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=12)
    
    # Write headers
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    # Write data
    for row_num, student in enumerate(students, 2):
        ws.cell(row=row_num, column=1).value = row_num - 1
        ws.cell(row=row_num, column=2).value = student.name
        ws.cell(row=row_num, column=3).value = student.phone
        ws.cell(row=row_num, column=4).value = student.email or ''
        ws.cell(row=row_num, column=5).value = student.course.name if student.course else ''
        ws.cell(row=row_num, column=6).value = student.admission_date.strftime('%d-%m-%Y')
        ws.cell(row=row_num, column=7).value = student.address or ''
        ws.cell(row=row_num, column=8).value = student.city or ''
        ws.cell(row=row_num, column=9).value = student.state or ''
        ws.cell(row=row_num, column=10).value = student.pincode or ''
        ws.cell(row=row_num, column=11).value = student.parent_name or ''
        ws.cell(row=row_num, column=12).value = student.parent_phone or ''
        ws.cell(row=row_num, column=13).value = student.qualification or ''
        ws.cell(row=row_num, column=14).value = student.date_of_birth.strftime('%d-%m-%Y') if student.date_of_birth else ''
        ws.cell(row=row_num, column=15).value = float(student.total_fees)
        ws.cell(row=row_num, column=16).value = float(student.paid_fees)
        ws.cell(row=row_num, column=17).value = float(student.remaining_fees)
    
    # Adjust column widths
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # Save to BytesIO
    excel_file = BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)
    
    # Create response
    response = HttpResponse(
        excel_file.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    filename = f'admitted_students_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response