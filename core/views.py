from datetime import timedelta, datetime as dt, date
from django.db import transaction
import uuid  
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.html import escape
from django.db.models.functions import ExtractYear
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
import csv
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from io import BytesIO
from datetime import datetime
from decimal import Decimal, InvalidOperation
import json
import shutil
import os
import zipfile
from PIL import Image
from django.db.models import Sum, Count, Q, F
from .models import Student, FeePayment, StudentFinanceDetail, Enquiry, AdmittedStudent, Course, SalesItem, Attendance, Batch
from .forms import EnquiryForm, AdmittedStudentForm, FeePaymentForm, CourseForm, BatchManagementForm, AttendanceForm
from .utils import number_to_words, get_time_slot_display, get_course_display, get_available_years_from_field, is_valid_mobile, is_valid_pincode, get_cached_courses
from .constants import TIME_SLOT_CHOICES, TIME_SLOT_DISPLAY_MAP, DEFAULT_PAGE_SIZE
from django.contrib.auth import authenticate, login as auth_login

# ================= CUSTOM LOGIN =================
def custom_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            auth_login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    
    return render(request, 'core/login.html')

# ================= CUSTOM LOGOUT =================
def custom_logout(request):
    logout(request)
    messages.success(request, "You have been logged out successfully!")
    return redirect('home')


# ================= HOME PAGE =================
def home(request):
    if request.method == "POST":
        form = EnquiryForm(request.POST)
        if form.is_valid():
            # Check for duplicate enquiry (within last 5 minutes)
            five_minutes_ago = timezone.now() - timedelta(minutes=5)
            duplicate = Enquiry.objects.filter(
                name__iexact=form.cleaned_data['name'],
                mobile=form.cleaned_data['mobile'],
                created_at__gte=five_minutes_ago
            ).exists()
            
            if duplicate:
                messages.warning(request, "⚠️ Similar enquiry already submitted recently!")
            else:
                form.save()
                messages.success(request, "✅ Enquiry submitted successfully!")
            
            return redirect("home")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"❌ {field}: {error}")
            return redirect("home")

    form = EnquiryForm()
    all_courses = Course.objects.all().order_by('name')
    
    return render(request, "core/home.html", {
        'form': form,
        'all_courses': all_courses
    })


# ================= DASHBOARD =================
@login_required
def dashboard(request):
    selected_year = request.GET.get('year', '')
    
    # Get available admission years (from admission_date, not entry date)
    available_years = (
        AdmittedStudent.objects
        .annotate(year=ExtractYear('admission_date'))  # Using admission_date for year selection
        .values_list('year', flat=True)
        .distinct()
        .order_by('-year')
    )
    
    students = AdmittedStudent.objects.all()
    
    # Filter students by admission year if selected
    if selected_year:
        students = students.filter(admission_date__year=selected_year)
    
    enquiries = Enquiry.objects.all()
    if selected_year:
        enquiries = enquiries.filter(created_at__year=selected_year)
    enquiry_count = enquiries.count()
    
    mscit_count = students.filter(course='MS-CIT').count()
    klic_count = students.exclude(course='MS-CIT').count()
    
    course_distribution = {}
    for student in students:
        course_name = student.custom_course if student.course == 'Other' and student.custom_course else student.course
        course_distribution[course_name] = course_distribution.get(course_name, 0) + 1
    
    # Prepare data for clustered bar chart: admissions by course for each month (based on admission_date)
    if selected_year:
        # Filter by admission year (not entry year)
        year_students = AdmittedStudent.objects.filter(admission_date__year=int(selected_year))
    else:
        current_year = datetime.now().year
        year_students = AdmittedStudent.objects.filter(admission_date__year=current_year)
    
    # Get unique courses
    unique_courses = set()
    for student in year_students:
        course_name = student.custom_course if student.course == 'Other' and student.custom_course else student.course
        unique_courses.add(course_name)
    unique_courses = sorted(list(unique_courses))
    
    # Create monthly data by course (based on admission_date)
    monthly_by_course = {}
    for course in unique_courses:
        monthly_by_course[course] = {str(i): 0 for i in range(1, 13)}
    
    # Populate with actual data using admission_date month
    for student in year_students:
        if student.admission_date:
            course_name = student.custom_course if student.course == 'Other' and student.custom_course else student.course
            # Get month from admission_date, not entry date
            month = str(student.admission_date.month)
            if course_name in monthly_by_course:
                monthly_by_course[course_name][month] += 1
    
    course_distribution_json = json.dumps(course_distribution)
    monthly_by_course_json = json.dumps(monthly_by_course)
    
    context = {
        "enquiry_count": enquiry_count,
        "mscit_count": mscit_count,
        "klic_count": klic_count,
        "available_years": available_years,
        "selected_year": selected_year,
        "active_page": "dashboard",
        "course_distribution": course_distribution_json,
        "monthly_by_course": monthly_by_course_json,
    }
    
    return render(request, "core/dashboard.html", context)


# ================= ENQUIRY LIST (SINGLE DEFINITION) =================
@login_required
def enquiry_list(request):
    # Handle POST request for adding new enquiry
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        mobile = request.POST.get("mobile", "").strip()
        education = request.POST.get("education", "").strip()
        course = request.POST.get("course", "").strip()
        custom_course = request.POST.get("other_course", "").strip()
        address = request.POST.get("address", "").strip()
        city = request.POST.get("city", "").strip()
        taluka = request.POST.get("taluka", "").strip()
        district = request.POST.get("district", "").strip()
        
        # VALIDATION
        if not name or not mobile or not education or not course:
            messages.error(request, "❌ Please fill all required fields!")
            return redirect("enquiry_list")
        
        if len(mobile) != 10 or not mobile.isdigit():
            messages.error(request, "❌ Mobile number must be 10 digits!")
            return redirect("enquiry_list")
        
        # CHECK FOR DUPLICATE ENQUIRY
        five_minutes_ago = timezone.now() - timedelta(minutes=5)
        
        duplicate = Enquiry.objects.filter(
            name__iexact=name,
            mobile=mobile,
            created_at__gte=five_minutes_ago
        ).exists()
        
        if duplicate:
            messages.error(request, "⚠️ This enquiry was already submitted recently!")
            return redirect("enquiry_list")
        
        # CREATE ENQUIRY
        enquiry = Enquiry.objects.create(
            name=name,
            mobile=mobile,
            education=education,
            course=course,
            custom_course=custom_course if course == "Other" else "",
            address=address,
            city=city,
            taluka=taluka,
            district=district
        )
        
        messages.success(request, f"✅ Enquiry submitted successfully!")
        return redirect("enquiry_list")
    
    # GET REQUEST - Display enquiries
    search = request.GET.get("search", "")
    month = request.GET.get("month", "")
    year = request.GET.get("year", "")
    course = request.GET.get("course", "")
    
    enquiries = Enquiry.objects.all().order_by("-created_at")
    
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
    
    available_years = (
        Enquiry.objects
        .annotate(year=ExtractYear('created_at'))
        .values_list('year', flat=True)
        .distinct()
        .order_by('-year')
    )
    
    available_courses = (
        Enquiry.objects
        .values_list('course', flat=True)
        .distinct()
        .order_by('course')
    )
    
    paginator = Paginator(enquiries, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    filters_query = ""
    if search:
        filters_query += f"&search={search}"
    if month:
        filters_query += f"&month={month}"
    if year:
        filters_query += f"&year={year}"
    if course:
        filters_query += f"&course={course}"
    
    all_courses = Course.objects.all().order_by('name')
    
    return render(request, "core/enquiries.html", {
        "page_obj": page_obj,
        "search": search,
        "month": month,
        "year": year,
        "course": course,
        "available_years": available_years,
        "available_courses": available_courses,
        "filters_query": filters_query,
        "active_page": "enquiries",
        "all_courses": all_courses
    })


# ================= DELETE ENQUIRY =================
@login_required
@staff_member_required
def delete_enquiry(request, id):
    enquiry = get_object_or_404(Enquiry, id=id)
    enquiry.delete()
    messages.success(request, "Enquiry deleted successfully")
    return redirect("enquiry_list")


# ================= EXPORT ENQUIRIES =================
@login_required
def export_enquiries(request):
    search = request.GET.get("search", "")
    month = request.GET.get("month", "")
    year = request.GET.get("year", "")
    course = request.GET.get("course", "")
    
    enquiries = Enquiry.objects.all().order_by("-created_at")
    
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
    
    response = HttpResponse(content_type="text/csv")
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    response["Content-Disposition"] = f'attachment; filename="enquiries_{timestamp}.csv"'

    writer = csv.writer(response)
    writer.writerow(["ID", "Name", "Mobile", "Education", "Course", "Address", "City", "Taluka", "District", "Date & Time"])

    for e in enquiries:
        writer.writerow([
            e.id,
            e.name,
            e.mobile,
            e.education,
            e.course,
            e.address or "",
            e.city or "",
            e.taluka or "",
            e.district or "",
            e.created_at.strftime("%d-%m-%Y %I:%M %p")
        ])

    return response


# ================= ENQUIRY DETAIL =================
@login_required
def enquiry_detail(request, id):
    """Return enquiry details as JSON"""
    enquiry = get_object_or_404(Enquiry, id=id)
    
    if enquiry.course == "Other" and enquiry.custom_course:
        display_course = enquiry.custom_course
    else:
        display_course = enquiry.course
    
    data = {
        'id': enquiry.id,
        'name': enquiry.name,
        'mobile': enquiry.mobile,
        'education': enquiry.education,
        'course': enquiry.course,
        'custom_course': enquiry.custom_course or '',
        'display_course': display_course,
        'address': enquiry.address or '',
        'city': enquiry.city or '',
        'taluka': enquiry.taluka or '',
        'district': enquiry.district or '',
        'created_at': enquiry.created_at.strftime('%d %B %Y, %I:%M %p'),
    }
    
    return JsonResponse(data)


# ================= CONVERT ENQUIRY TO ADMISSION =================
@login_required
def convert_enquiry_to_admission(request, id):
    """Convert enquiry to admission with pre-filled data"""
    enquiry = get_object_or_404(Enquiry, id=id)
    
    if enquiry.course == 'Other' and enquiry.custom_course:
        course_value = 'Other'
        custom_course_value = enquiry.custom_course
    else:
        course_value = enquiry.course
        custom_course_value = ''
    
    request.session['enquiry_conversion'] = {
        'enquiry_id': enquiry.id,
        'name': enquiry.name,
        'mobile': enquiry.mobile,
        'education': enquiry.education,
        'course': course_value,
        'custom_course': custom_course_value,
        'address': enquiry.address or '',
        'city': enquiry.city or '',
        'tehsil_block': enquiry.taluka or '',
        'district': enquiry.district or '',
    }
    
    return redirect('new_admission')


# ================= NEW ADMISSION =================
@login_required
def new_admission(request):
    if request.method == "POST":
        form = AdmittedStudentForm(request.POST, request.FILES)
        if form.is_valid():
            admission = form.save(commit=False)
            admission.save()
            messages.success(request, f"✅ Admission for {admission.full_name} has been successfully recorded! Total Fees: ₹{admission.total_fees}")
            return redirect("new_admission")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"❌ {field}: {error}")
    else:
        form = AdmittedStudentForm()
    
    # Get enquiry data from session if available
    enquiry_data = request.session.get('enquiry_conversion', {})
    
    # Get all courses from database
    all_courses = Course.objects.all().order_by('name')
    
    return render(request, "core/new_admission.html", {
        "active_page": "new_admission",
        "form": form,
        "enquiry_data": enquiry_data,
        "all_courses": all_courses
    })


# ================= IMPORT ADMISSIONS FROM EXCEL =================
@login_required
@staff_member_required
@require_http_methods(["POST"])
@csrf_protect
def import_admissions_excel(request):
    """Import multiple admissions from Excel file"""
    try:
        if 'excel_file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No file uploaded'
            }, status=400)
        
        excel_file = request.FILES['excel_file']
        
        # Validate file extension
        if not excel_file.name.lower().endswith(('.xlsx', '.xls')):
            return JsonResponse({
                'success': False,
                'error': 'Invalid file format. Please upload an Excel file (.xlsx or .xls)'
            }, status=400)
        
        # Load the Excel file
        try:
            wb = openpyxl.load_workbook(excel_file)
            ws = wb.active
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error reading Excel file: {str(e)}'
            }, status=400)
        
        # Expected headers - matches actual Excel format from screenshots
        expected_headers = [
            'S.No', 'Full Name', 'Student Name', 'Father Name', 'Surname', 'Mother Name',
            'Date of Birth', 'Mobile (Own)', 'Parent Mobile', 'Gender', 'Marital Status',
            'Course', 'Batch Month', 'Batch Year', 'Educational Qualification',
            'Address', 'City', 'Tehsil/Block', 'District', 'Pin Code',
            'Total Fees (₹)', 'Paid Fees First Installment', 'Admission Date'
        ]
        
        # Verify headers
        file_headers = [cell.value for cell in ws[1]]
        
        # Check if the headers match the expected format
        if file_headers != expected_headers:
            return JsonResponse({
                'success': False,
                'error': 'Invalid Excel format. Headers do not match the expected format. Please use the correct template from "Export Admitted Students".'
            }, status=400)
        
        # Import rows
        imported_count = 0
        error_rows = []
        
        with transaction.atomic():
            for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=False), start=2):
                try:
                    # Extract values from row
                    row_values = [cell.value for cell in row]
                    
                    # Skip empty rows
                    if not any(row_values):
                        continue
                    
                    # Handle the export format - Updated to match actual Excel headers
                    # Columns: S.No(0), Full Name(1), Student Name(2), Father Name(3), Surname(4), Mother Name(5),
                    # Date of Birth(6), Mobile(7), Parent Mobile(8), Gender(9), Marital Status(10),
                    # Course(11), Batch Month(12), Batch Year(13), Educational Qualification(14),
                    # Address(15), City(16), Tehsil/Block(17), District(18), Pin Code(19),
                    # Total Fees(20), Paid Fees First Installment(21), Admission Date(22)
                    
                    full_name = row_values[1]
                    student_name = row_values[2]
                    father_name = row_values[3]
                    surname = row_values[4]
                    mother_name = row_values[5]
                    dob_str = row_values[6]
                    mobile_own = row_values[7]
                    parent_mobile = row_values[8]
                    gender = row_values[9]
                    marital_status = row_values[10]
                    course = row_values[11]
                    batch_month = row_values[12]
                    batch_year = row_values[13]
                    educational_qualification = row_values[14]
                    address = row_values[15]
                    city = row_values[16]
                    tehsil_block = row_values[17]
                    district = row_values[18]
                    pin_code = row_values[19]
                    total_fees_val = row_values[20]
                    first_installment_val = row_values[21]
                    admission_date_str = row_values[22]
                    custom_course = None
                    payment_mode = 'Cash'  # Default payment mode
                    
                    # Validate required fields
                    required_fields = {
                        'Student Name': student_name,
                        'Father Name': father_name,
                        'Surname': surname,
                        'Full Name': full_name,
                        'Mobile (Own)': mobile_own,
                        'Gender': gender,
                        'Marital Status': marital_status,
                        'Course': course,
                        'Address': address,
                        'City': city,
                        'Tehsil/Block': tehsil_block,
                        'District': district,
                        'Pin Code': pin_code,
                        'Educational Qualification': educational_qualification
                    }
                    
                    missing_fields = [name for name, value in required_fields.items() if not value]
                    
                    if missing_fields:
                        error_rows.append({
                            'row': row_num,
                            'error': f'Missing required fields: {", ".join(missing_fields[:3])}'
                        })
                        continue
                    
                    # Parse date of birth
                    try:
                        if isinstance(dob_str, str):
                            dob = datetime.strptime(dob_str, '%d-%m-%Y').date()
                        else:
                            dob = dob_str
                    except (ValueError, TypeError):
                        error_rows.append({
                            'row': row_num,
                            'error': 'Invalid date format for Date of Birth. Use DD-MM-YYYY'
                        })
                        continue
                    
                    # Parse admission date
                    try:
                        if isinstance(admission_date_str, str):
                            # Handle both formats: 'DD-MM-YYYY' and 'DD-MM-YYYY HH:MM AM/PM'
                            if ' ' in admission_date_str:
                                admission_date = datetime.strptime(admission_date_str, '%d-%m-%Y %I:%M %p').date()
                            else:
                                admission_date = datetime.strptime(admission_date_str, '%d-%m-%Y').date()
                        else:
                            admission_date = admission_date_str
                    except (ValueError, TypeError):
                        admission_date = date.today()
                    
                    # Parse fees
                    try:
                        total_fees = Decimal(str(total_fees_val)) if total_fees_val else Decimal('5000')
                    except (ValueError, InvalidOperation):
                        total_fees = Decimal('5000')
                    
                    # Parse first installment
                    try:
                        first_installment = Decimal(str(first_installment_val)) if first_installment_val else Decimal('0')
                    except (ValueError, InvalidOperation):
                        first_installment = Decimal('0')
                    
                    # Validate mobile
                    mobile_str = str(mobile_own).strip()
                    if not is_valid_mobile(mobile_str):
                        error_detail = 'Mobile must be 10 digits starting with 6, 7, 8, or 9'
                        error_rows.append({
                            'row': row_num,
                            'field': 'Mobile (Own)',
                            'value': mobile_own,
                            'error': error_detail
                        })
                        continue
                    
                    # Validate pin code
                    pin_str = str(pin_code).strip()
                    if not is_valid_pincode(pin_str):
                        error_detail = 'Pin code must be exactly 6 digits'
                        error_rows.append({
                            'row': row_num,
                            'field': 'Pin Code',
                            'value': pin_code,
                            'error': error_detail
                        })
                        continue
                    
                    # Check if student already exists (by full_name and mobile)
                    existing = AdmittedStudent.objects.filter(
                        full_name__iexact=full_name,
                        mobile_own=mobile_str
                    ).exists()
                    
                    if existing:
                        error_rows.append({
                            'row': row_num,
                            'field': 'Full Name + Mobile',
                            'value': f'{full_name} ({mobile_own})',
                            'error': 'Duplicate student - already exists in database'
                        })
                        continue
                    
                    # Create admission record
                    admission = AdmittedStudent.objects.create(
                        student_name=student_name[:100],
                        father_name=father_name[:100],
                        surname=surname[:100],
                        mother_name=mother_name[:100] if mother_name else '',
                        full_name=full_name[:300],
                        date_of_birth=dob,
                        mobile_own=mobile_str,
                        parent_mobile=str(parent_mobile).strip() if parent_mobile else '',
                        gender=gender,
                        marital_status=marital_status,
                        course=course,
                        custom_course=custom_course[:100] if custom_course else '',
                        educational_qualification=educational_qualification[:200],
                        address=address,
                        city=city[:100],
                        tehsil_block=tehsil_block[:100],
                        district=district[:100],
                        pin_code=pin_str,
                        batch_month=str(batch_month).strip() if batch_month else None,
                        batch_year=str(batch_year).strip() if batch_year else None,
                        total_fees=total_fees,
                        paid_fees=Decimal('0'),
                        admission_date=admission_date
                    )
                    
                    # Create FeePayment receipt if first_installment > 0 and payment_mode is valid
                    valid_payment_modes = ['Cash', 'UPI', 'Card', 'Bank Transfer']
                    if first_installment > Decimal('0') and payment_mode in valid_payment_modes:
                        # Generate unique receipt_no: REC-DDMMYYYY-XXXXX
                        receipt_prefix = admission_date.strftime('%d%m%Y')
                        receipt_suffix = str(uuid.uuid4().hex[:5]).upper()
                        receipt_no = f'REC-{receipt_prefix}-{receipt_suffix}'
                        
                        # Create FeePayment record
                        FeePayment.objects.create(
                            receipt_no=receipt_no,
                            student=admission,
                            amount=first_installment,
                            payment_mode=payment_mode,
                            payment_date=admission_date,
                            total_fees_at_payment=total_fees,
                            paid_before_this=Decimal('0'),
                            remaining_after_this=total_fees - first_installment
                        )
                        
                        # Update admission paid_fees to reflect this payment
                        admission.paid_fees = first_installment
                        admission.save(update_fields=['paid_fees'])
                    
                    imported_count += 1
                    
                except Exception as e:
                    error_rows.append({
                        'row': row_num,
                        'error': str(e)[:100]
                    })
                    continue
        
        # Prepare response
        success_message = f'✅ Successfully imported {imported_count} admission(s)'
        
        if error_rows:
            error_message = f'⚠️ {len(error_rows)} row(s) had errors'
            return JsonResponse({
                'success': True,
                'imported_count': imported_count,
                'error_count': len(error_rows),
                'message': success_message,
                'warning': error_message,
                'errors': error_rows[:10]  # Return first 10 errors
            })
        else:
            return JsonResponse({
                'success': True,
                'imported_count': imported_count,
                'message': success_message
            })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)


# ================= IMPORT STUDENT PHOTOS FROM ZIP =================
@login_required
@staff_member_required
@csrf_protect
@require_http_methods(['POST'])
def import_student_photos_zip(request):
    """Import student photos from ZIP file - matches by surname and name"""
    try:
        zip_file = request.FILES.get('zip_file')
        
        if not zip_file:
            return JsonResponse({
                'success': False,
                'message': 'Please select a ZIP file'
            }, status=400)
        
        matched = 0
        mismatched = []
        errors = []
        
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            for file_info in zip_ref.filelist:
                # Skip directories and hidden files
                if file_info.is_dir() or file_info.filename.startswith('__'):
                    continue
                
                filename = os.path.basename(file_info.filename)
                name_without_ext = os.path.splitext(filename)[0].strip()
                
                # Parse surname and name from filename
                # Expected format: "Surname Name.jpg" or "surname_name.jpg"
                # Try space separator first, then underscore
                parts = None
                if ' ' in name_without_ext:
                    parts = name_without_ext.split(' ', 1)
                elif '_' in name_without_ext:
                    parts = name_without_ext.split('_', 1)
                else:
                    # Single name, try to match with student_name
                    students = AdmittedStudent.objects.filter(
                        student_name__icontains=name_without_ext
                    )
                    if not students.exists():
                        mismatched.append(f"{filename} (Expected: 'Surname Name.jpg')")
                        continue
                    if students.count() > 1:
                        errors.append(f"{filename}: Multiple students match. Use 'Surname Name' format")
                        continue
                    parts = None
                
                if parts and len(parts) == 2:
                    surname, student_name = parts[0].strip(), parts[1].strip()
                    
                    # Search for student by surname AND name (case-insensitive)
                    students = AdmittedStudent.objects.filter(
                        surname__icontains=surname,
                        student_name__icontains=student_name
                    )
                elif parts is None and len(mismatched) > 0:
                    # Already handled above, skip
                    continue
                else:
                    mismatched.append(f"{filename} (Expected: 'Surname Name.jpg')")
                    continue
                
                if not students.exists():
                    mismatched.append(f"{filename} (No match: {surname} {student_name})")
                    continue
                
                if students.count() > 1:
                    errors.append(f"{filename}: {students.count()} students match. Be more specific")
                    continue
                
                student = students.first()
                
                # Read and validate image
                try:
                    file_content = zip_ref.read(file_info.filename)
                    
                    # Validate it's a real image
                    img = Image.open(BytesIO(file_content))
                    img.verify()
                    
                    # Save photo
                    file_extension = os.path.splitext(filename)[1].lower()
                    photo_name = f"student_photos/{student.id}_{student.surname}_{student.student_name}{file_extension}"
                    
                    # Remove old photo if exists
                    if student.photo:
                        student.photo.delete()
                    
                    # Save new photo
                    from django.core.files.base import ContentFile
                    student.photo.save(
                        photo_name,
                        ContentFile(file_content),
                        save=True
                    )
                    matched += 1
                    
                except Exception as e:
                    errors.append(f"{filename}: Invalid image file - {str(e)[:50]}")
        
        return JsonResponse({
            'success': True,
            'message': f'{matched} photos imported successfully',
            'matched': matched,
            'mismatched': mismatched,
            'errors': errors,
            'mismatched_count': len(mismatched),
            'error_count': len(errors)
        })
    
    except zipfile.BadZipFile:
        return JsonResponse({
            'success': False,
            'message': 'Invalid ZIP file. Please upload a valid ZIP file.',
            'matched': 0,
            'mismatched': [],
            'errors': []
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}',
            'matched': 0,
            'mismatched': [],
            'errors': []
        }, status=500)


# ================= ADD COURSE TO DATABASE (SINGLE DEFINITION) =================
@login_required
@require_http_methods(["POST"])
@csrf_protect
def add_course_ajax(request):
    """Add a new course via AJAX"""
    try:
        data = json.loads(request.body)
        course_name = data.get('course_name', '').strip()
        
        # Validate using CourseForm
        form = CourseForm(data={'name': course_name, 'duration': 'To be defined'})
        
        if form.is_valid():
            course = form.save()
            return JsonResponse({
                'success': True,
                'message': f'Course "{course_name}" added successfully!',
                'course_id': course.id,
                'course_name': course.name
            }, status=201)
        else:
            errors = [str(error) for field_errors in form.errors.values() for error in field_errors]
            return JsonResponse({
                'success': False,
                'message': ' | '.join(errors) if errors else 'Invalid course data'
            }, status=400)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


# ================= ADMITTED STUDENTS LIST =================
@login_required
def admitted_students(request):
    search = request.GET.get("search", "")
    month = request.GET.get("month", "")
    year = request.GET.get("year", "")
    course = request.GET.get("course", "")
    batch_month = request.GET.get("batch_month", "")  # NEW
    batch_year = request.GET.get("batch_year", "")    # NEW
    
    # Optimized query with only required fields to reduce database hits
    students = AdmittedStudent.objects.only(
        'id', 'full_name', 'student_name', 'father_name', 'surname', 'mobile_own', 'course', 
        'admission_date', 'city', 'total_fees', 'paid_fees', 'photo', 'batch_month', 'batch_year'
    ).order_by('surname', 'student_name')
    
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
    
    # NEW: Batch filters
    if batch_month:
        students = students.filter(batch_month=batch_month)
    
    if batch_year:
        students = students.filter(batch_year=batch_year)
    
    # Optimized: Use values_list instead of full objects for dropdown data
    available_years = (
        AdmittedStudent.objects
        .annotate(year=ExtractYear('admission_date'))
        .values_list('year', flat=True)
        .distinct()
        .order_by('-year')
    )
    
    # NEW: Get available batch months and years (optimized)
    available_batch_months = (
        AdmittedStudent.objects
        .exclude(batch_month__isnull=True)
        .exclude(batch_month='')
        .values_list('batch_month', flat=True)
        .distinct()
        .order_by('batch_month')
    )
    
    available_batch_years = (
        AdmittedStudent.objects
        .exclude(batch_year__isnull=True)
        .exclude(batch_year='')
        .values_list('batch_year', flat=True)
        .distinct()
        .order_by('-batch_year')
    )
    
    # Optimized: Cache courses (small table, rarely changes)
    all_courses = get_cached_courses()
    
    return render(request, 'core/admitted_students.html', {
        'students': students,
        'search': search,
        'month': month,
        'year': year,
        'course': course,
        'batch_month': batch_month,  # NEW
        'batch_year': batch_year,    # NEW
        'available_years': available_years,
        'available_batch_months': available_batch_months,  # NEW
        'available_batch_years': available_batch_years,    # NEW
        'active_page': 'admitted_students',
        'all_courses': all_courses
    })



# ================= STUDENT DETAIL (ADMITTED) =================
@login_required
def student_detail_admitted(request, student_id):
    """Get admitted student details via AJAX"""
    try:
        student = AdmittedStudent.objects.get(id=student_id)
        
        # Get payment history
        fee_payments = FeePayment.objects.filter(student=student).order_by('payment_date')
        payment_history = []
        
        for payment in fee_payments:
            # Note: payment_date is now a DateField (no time component)
            payment_history.append({
                'id': payment.id,
                'payment_date': payment.payment_date.strftime('%d-%m-%Y') if payment.payment_date else '',
                'payment_time': '',  # No time for DateField
                'amount': float(payment.amount),
                'payment_mode': payment.payment_mode,
                'receipt_no': payment.receipt_no or '',
                'remaining_after': float(payment.remaining_after_this),
            })
        
        # ✅ Include ALL fields from the form
        data = {
            'id': student.id,
            'student_name': student.student_name,
            'father_name': student.father_name,
            'surname': student.surname,
            'mother_name': student.mother_name,
            'full_name': student.full_name,
            'date_of_birth': student.date_of_birth.strftime('%Y-%m-%d') if student.date_of_birth else '',
            'gender': student.gender,
            'marital_status': student.marital_status,
            'mobile_own': student.mobile_own,
            'parent_mobile': student.parent_mobile or '',
            'course': student.course,
            'custom_course': student.custom_course or '',
            'educational_qualification': student.educational_qualification,
            'batch_month': student.batch_month or '',
            'batch_year': student.batch_year or '',
            'batch_display': student.batch_display or 'Not Assigned',
            'address': student.address,
            'city': student.city,
            'tehsil_block': student.tehsil_block,
            'district': student.district,
            'pin_code': student.pin_code,
            'photo': student.photo.url if student.photo else None,
            'total_fees': float(student.total_fees),
            'paid_fees': float(student.paid_fees),
            'remaining_fees': float(student.remaining_fees),
            'admission_date': student.admission_date.strftime('%Y-%m-%d') if student.admission_date else '',
            'payment_history': payment_history,
        }
        
        return JsonResponse(data)
    except AdmittedStudent.DoesNotExist:
        return JsonResponse({'error': 'Student not found'}, status=404)
    except Exception as e:
        print(f"Error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

# ================= UPDATE STUDENT (ADMITTED) =================
@login_required
def update_student_admitted(request, student_id):
    if request.method == 'POST':
        student = get_object_or_404(AdmittedStudent, id=student_id)
        
        # Handle both JSON and POST form data
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
        else:
            data = request.POST.dict()
        
        # Only update fields that are provided
        if 'student_name' in data:
            student.student_name = data.get('student_name')
        if 'father_name' in data:
            student.father_name = data.get('father_name')
        if 'surname' in data:
            student.surname = data.get('surname')
        if 'mother_name' in data:
            student.mother_name = data.get('mother_name')
        if 'full_name' in data:
            student.full_name = data.get('full_name')
        if 'date_of_birth' in data:
            student.date_of_birth = data.get('date_of_birth')
        if 'admission_date' in data:
            student.admission_date = data.get('admission_date')
        if 'mobile_own' in data:
            student.mobile_own = data.get('mobile_own')
        if 'parent_mobile' in data:
            student.parent_mobile = data.get('parent_mobile')
        if 'gender' in data:
            student.gender = data.get('gender')
        if 'marital_status' in data:
            student.marital_status = data.get('marital_status')
        if 'course' in data:
            student.course = data.get('course')
        if 'custom_course' in data:
            student.custom_course = data.get('custom_course')
        if 'educational_qualification' in data:
            student.educational_qualification = data.get('educational_qualification')
        if 'address' in data:
            student.address = data.get('address')
        if 'city' in data:
            student.city = data.get('city')
        if 'tehsil_block' in data:
            student.tehsil_block = data.get('tehsil_block')
        if 'district' in data:
            student.district = data.get('district')
        if 'pin_code' in data:
            student.pin_code = data.get('pin_code')
        
        # Update batch information
        if 'batch_month' in data:
            student.batch_month = data.get('batch_month', '')
        if 'batch_year' in data:
            student.batch_year = data.get('batch_year', '')
        if 'theory_batch_time' in data:
            student.theory_batch_time = data.get('theory_batch_time', '')
        if 'practical_batch_time' in data:
            student.practical_batch_time = data.get('practical_batch_time', '')
        
        # Update fees information
        if 'total_fees' in data:
            total_fees = data.get('total_fees')
            if total_fees:
                student.total_fees = Decimal(total_fees)
        
        # Handle photo removal flag
        if data.get('remove_photo') == 'true':
            print(f'[PHOTO DEBUG] Remove photo flag detected')
            if student.photo:
                try:
                    print(f'[PHOTO DEBUG] Deleting photo: {student.photo}')
                    student.photo.delete()
                    student.photo = None
                except Exception as e:
                    print(f'[PHOTO DEBUG] Error deleting photo: {e}')
        # Handle photo upload (only if not removing)
        elif 'photo' in request.FILES:
            photo_file = request.FILES['photo']
            print(f'[PHOTO DEBUG] Photo file found: {photo_file.name} ({photo_file.size} bytes)')
            # Delete old photo if it exists
            if student.photo:
                try:
                    print(f'[PHOTO DEBUG] Deleting old photo: {student.photo}')
                    student.photo.delete()
                except Exception as e:
                    print(f'[PHOTO DEBUG] Error deleting old photo: {e}')
            # Save new photo
            student.photo = photo_file
            print(f'[PHOTO DEBUG] Photo assigned to student')
        else:
            print(f'[PHOTO DEBUG] No photo action. Remove flag: {data.get("remove_photo")}, Files: {list(request.FILES.keys())}')
        
        student.save()
        
        # Update StudentFinanceDetail if total_fees changed
        if 'total_fees' in data:
            total_fees = data.get('total_fees')
            if total_fees:
                finance_detail, created = StudentFinanceDetail.objects.get_or_create(student=student)
                finance_detail.save()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

# ================= SEARCH ADMITTED STUDENTS (AJAX) =================
@login_required
def search_admitted_students(request):
    query = request.GET.get('q', '').strip()
    
    if len(query) < 3:
        return JsonResponse({'students': []})
    
    students = AdmittedStudent.objects.filter(
        Q(full_name__icontains=query) |
        Q(student_name__icontains=query) |
        Q(mobile_own__icontains=query)
    ).order_by('-admission_date')[:10]
    
    students_data = []
    for student in students:
        course_name = student.custom_course if student.course == 'Other' and student.custom_course else student.course
        students_data.append({
            'id': student.id,
            'full_name': escape(student.full_name or f"{student.student_name} {student.father_name} {student.surname}"),
            'mobile_own': escape(student.mobile_own or ''),
            'course': escape(course_name or ''),
        })
    
    return JsonResponse({'students': students_data})

# ================= FEES PAYMENT PAGE =================
@login_required
def fees_payment(request):
    return render(request, 'core/fees_payment.html', {
        'active_page': 'fees_payment'
    })


# ================= SEARCH STUDENTS FOR FEES PAYMENT =================
@login_required
def search_students_for_payment(request):
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'students': []})
    
    students = AdmittedStudent.objects.filter(
        Q(full_name__icontains=query) |
        Q(student_name__icontains=query) |
        Q(mobile_own__icontains=query)
    ).order_by('full_name')[:10]
    
    students_data = []
    for student in students:
        course_name = student.custom_course if student.course == 'Other' and student.custom_course else student.course
        students_data.append({
            'id': student.id,
            'full_name': escape(student.full_name or ''),
            'mobile_own': escape(student.mobile_own or ''),
            'course': escape(course_name or '')
        })
    
    return JsonResponse({'students': students_data})


# ================= SUBMIT FEE PAYMENT - FIXED VERSION WITH BATCH =================
@login_required
@csrf_protect
@require_http_methods(["POST"])
def submit_fee_payment(request):
    if request.method == 'POST':
        try:
            # Get form data
            student_id = request.POST.get('student_id')
            amount = request.POST.get('amount')
            payment_mode = request.POST.get('payment_mode')
            payment_date = request.POST.get('payment_date')
            remarks = request.POST.get('remarks', '')
            
            # Debug logging
            print(f"Received payment data: student_id={student_id}, amount={amount}, payment_mode={payment_mode}, payment_date={payment_date}")
            
            # Validate with FeePaymentForm
            form_data = {
                'student': student_id,
                'amount': amount,
                'payment_mode': payment_mode,
                'payment_date': payment_date,
                'remarks': remarks
            }
            form = FeePaymentForm(form_data)
            
            if not form.is_valid():
                errors = [str(error) for field_errors in form.errors.values() for error in field_errors]
                return JsonResponse({
                    'success': False,
                    'error': ' | '.join(errors) if errors else 'Invalid payment data'
                }, status=400)
            
            # Parse payment_date string (YYYY-MM-DD format) to date object
            try:
                from datetime import datetime
                payment_date_obj = datetime.strptime(payment_date, '%Y-%m-%d').date()
                payment_date_formatted = payment_date_obj.strftime('%d-%m-%Y')
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid payment date format'
                }, status=400)
            
            # Convert amount to Decimal
            try:
                amount = Decimal(str(amount).strip())
                # Validate amount is positive
                if amount <= 0:
                    raise ValueError("Amount must be greater than zero")
                # Validate amount doesn't exceed maximum (₹10 million)
                if amount > Decimal('10000000'):
                    raise ValueError("Amount exceeds maximum limit (₹10,000,000)")
                # Quantize to 2 decimal places (paise)
                amount = amount.quantize(Decimal('0.01'))
            except (ValueError, TypeError) as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Invalid amount: {str(e)}'
                }, status=400)
            
            # Use atomic transaction
            with transaction.atomic():
                # Get student with lock
                try:
                    student = AdmittedStudent.objects.select_for_update().get(id=student_id)
                except AdmittedStudent.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'Student not found'
                    }, status=404)
                
                # Check if amount exceeds remaining fees
                if amount > student.remaining_fees:
                    return JsonResponse({
                        'success': False,
                        'error': f'Payment amount (₹{amount}) cannot exceed remaining fees (₹{student.remaining_fees})'
                    }, status=400)
                
                # Create payment record with user-selected payment date
                payment = FeePayment.objects.create(
                    student=student,
                    amount=amount,
                    payment_mode=payment_mode,
                    payment_date=payment_date_obj,
                    remarks=remarks,
                    total_fees_at_payment=student.total_fees,
                    paid_before_this=student.paid_fees,
                    remaining_after_this=student.total_fees - (student.paid_fees + amount)
                )
                
                # Update student's paid fees using F() for atomic increment
                student.paid_fees = F('paid_fees') + amount
                student.save(update_fields=['paid_fees'])
                
                # Prepare receipt data
                course_name = student.custom_course if student.course == 'Other' and student.custom_course else student.course
                
                # ✅ FIXED: Get batch information correctly
                batch_month = student.batch_month or ''
                batch_year = student.batch_year or ''
                
                # Create batch display string
                if batch_month and batch_year:
                    batch_display = f"{batch_month} {batch_year}"
                else:
                    batch_display = "Not Assigned"
                
                receipt_data = {
                    'receipt_no': payment.receipt_no,
                    'date': payment_date_formatted,
                    'time': '',  # No time for DateField
                    'student_name': student.full_name,
                    'course': course_name,
                    'batch': batch_display,  # ✅ CORRECTED: Use batch_display
                    'mobile': student.mobile_own,
                    'payment_mode': payment_mode,
                    'total_fees': f"{float(student.total_fees):.2f}",
                    'previous_paid': f"{float(payment.paid_before_this):.2f}",
                    'amount_paid': f"{float(amount):.2f}",
                    'remaining_fees': f"{float(payment.remaining_after_this):.2f}",
                    'amount_in_words': number_to_words(float(amount))
                }
                
                print(f"Payment successful! Receipt: {receipt_data['receipt_no']}")
                print(f"Batch info: {batch_display}")
                
                return JsonResponse({
                    'success': True,
                    'receipt': receipt_data,
                    'message': 'Payment recorded successfully'
                })
                
        except Exception as e:
            print(f"Error in submit_fee_payment: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': f'Server error: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method. Use POST.'
    }, status=405)

# ================= NUMBER TO WORDS CONVERTER =================
def number_to_words(num):
    """Convert number to words for Indian currency"""
    ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine']
    tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']
    teens = ['Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 
             'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen']
    
    if num == 0:
        return 'Zero Rupees Only'
    
    def convert_less_than_thousand(n):
        if n == 0:
            return ''
        
        result = ''
        
        if n >= 100:
            result += ones[n // 100] + ' Hundred '
            n %= 100
        
        if n >= 20:
            result += tens[n // 10] + ' '
            n %= 10
        elif n >= 10:
            result += teens[n - 10] + ' '
            return result
        
        if n > 0:
            result += ones[n] + ' '
        
        return result
    
    rupees = int(num)
    paise = int(round((num - rupees) * 100))
    
    result = ''
    
    if rupees >= 10000000:
        result += convert_less_than_thousand(rupees // 10000000) + 'Crore '
        rupees %= 10000000
    
    if rupees >= 100000:
        result += convert_less_than_thousand(rupees // 100000) + 'Lakh '
        rupees %= 100000
    
    if rupees >= 1000:
        result += convert_less_than_thousand(rupees // 1000) + 'Thousand '
        rupees %= 1000
    
    if rupees > 0:
        result += convert_less_than_thousand(rupees)
    
    result += 'Rupees'
    
    if paise > 0:
        result += ' and ' + convert_less_than_thousand(paise) + 'Paise'
    
    result += ' Only'
    
    return result.strip()


# ================= EXPORT STUDENTS TO EXCEL =================
@login_required
def export_students_excel(request):
    students = AdmittedStudent.objects.all().order_by('-admission_date')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Admitted Students"

    headers = ['S.No','Full Name','Mobile','Course','Total Fees','Paid Fees','Remaining Fees','Admission Date']
    ws.append(headers)

    for i, s in enumerate(students, 1):
        course = s.custom_course if s.course == 'Other' else s.course
        ws.append([
            i,
            s.full_name,
            s.mobile_own,
            course,
            float(s.total_fees),
            float(s.paid_fees),
            float(s.remaining_fees),
            s.admission_date.strftime('%d-%m-%Y')
        ])

    file = BytesIO()
    wb.save(file)
    file.seek(0)

    response = HttpResponse(file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=students_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    return response


# ================= RECEIPTS VIEW =================
@login_required
def receipts_view(request):
    """Main receipts page"""
    return render(request, 'core/receipts.html', {
        'active_page': 'receipts'
    })



# ================= UPDATE RECEIPT API =================
@login_required
def get_receipts(request):
    """API endpoint to get receipts with filters"""
    try:
        receipts = FeePayment.objects.select_related('student').all().order_by('-payment_date')
        
        # Prepare receipt data
        receipt_list = []
        for receipt in receipts:
            student = receipt.student
            
            # ✅ Get batch information
            batch_month = student.batch_month or ''
            batch_year = student.batch_year or ''
            
            if batch_month and batch_year:
                batch_display = f"{batch_month} {batch_year}"
            else:
                batch_display = "Not Assigned"
            
            # Get course name (custom if 'Other' selected)
            course_name = student.custom_course if student.course == 'Other' and student.custom_course else student.course
            
            receipt_list.append({
                'id': receipt.id,
                'receipt_no': receipt.receipt_no,
                'student_name': student.full_name,
                'course': course_name,
                'batch': batch_display,  # ✅ ADDED BATCH
                'batch_display': batch_display,  # ✅ Fallback
                'mobile': student.mobile_own,
                'payment_mode': receipt.payment_mode,
                'payment_date': str(receipt.payment_date),  # Convert DateField to string (YYYY-MM-DD)
                'payment_time': '',  # No time for DateField
                'paid_fees': float(receipt.amount),
                'paid_before_this': float(receipt.paid_before_this),
                'total_fees': float(student.total_fees),
                'remaining_fees': float(receipt.remaining_after_this),
            })
        
        return JsonResponse({
            'success': True,
            'receipts': receipt_list
        })
    except Exception as e:
        print(f"Error in get_receipts: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# ================= UPDATE RECEIPT API =================
@login_required
@require_http_methods(["POST"])
def update_receipt(request, receipt_id):
    """API endpoint to update a receipt"""
    try:
        data = json.loads(request.body)
        
        payment = FeePayment.objects.get(id=receipt_id)
        
        # Update only allowed fields
        if 'payment_date' in data:
            # Parse date string if it comes in YYYY-MM-DD format
            try:
                from datetime import datetime
                payment_date_str = data['payment_date']
                if isinstance(payment_date_str, str):
                    payment.payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()
                else:
                    payment.payment_date = payment_date_str
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid payment date format'
                }, status=400)
        
        if 'amount' in data or 'paid_fees' in data:
            old_amount = payment.amount
            try:
                new_amount = Decimal(str(data.get('amount') or data.get('paid_fees', old_amount)).strip())
            except (ValueError, TypeError, InvalidOperation):
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid amount format'
                }, status=400)
            
            # Validate amount
            if new_amount <= 0:
                return JsonResponse({
                    'success': False,
                    'error': 'Amount must be greater than zero'
                }, status=400)
            
            if new_amount > Decimal('10000000'):
                return JsonResponse({
                    'success': False,
                    'error': 'Amount exceeds maximum limit'
                }, status=400)
            
            # Update student's paid fees with validation
            student = payment.student
            amount_difference = new_amount - old_amount
            new_paid_fees = student.paid_fees + amount_difference
            
            # Validate new amount doesn't exceed total fees
            if new_paid_fees < 0:
                return JsonResponse({
                    'success': False,
                    'error': 'Cannot update: would result in negative paid fees'
                }, status=400)
            
            if new_paid_fees > student.total_fees:
                return JsonResponse({
                    'success': False,
                    'error': f'Cannot update: would exceed total fees'
                }, status=400)
            
            with transaction.atomic():
                # Use F() for atomic update
                student.paid_fees = F('paid_fees') + amount_difference
                student.save(update_fields=['paid_fees'])
                
                payment.amount = new_amount
                payment.remaining_after_this = student.total_fees - new_paid_fees
                payment.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Receipt updated successfully'
        })
        
    except FeePayment.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Receipt not found'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        print(f"Error updating receipt: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error: {str(e)}'
        }, status=500)
    
# ================= DELETE RECEIPT API =================
@login_required
@staff_member_required
@require_http_methods(["POST"])
def delete_receipt(request, receipt_id):
    """API endpoint to delete a receipt"""
    from datetime import date
    
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Invalid request method'
        }, status=405)
    
    try:
        payment = FeePayment.objects.select_related('student').get(id=receipt_id)
        payment_amount = payment.amount
        student = payment.student
        receipt_no = payment.receipt_no
        
        with transaction.atomic():
            # Ensure admission_date is set before saving
            if not student.admission_date:
                student.admission_date = date.today()
            
            student.paid_fees = max(0, student.paid_fees - payment_amount)
            student.save()
            payment.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Receipt {receipt_no} deleted successfully'
        })
        
    except FeePayment.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Receipt not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error deleting receipt: {str(e)}'
        }, status=500)


# ================= EXPORT RECEIPTS API =================
@login_required
def export_receipts(request):
    """Export receipts to Excel"""
    try:
        search = request.GET.get('search', '')
        date_filter = request.GET.get('date', '')
        month = request.GET.get('month', '')
        year = request.GET.get('year', '')
        
        payments = FeePayment.objects.select_related('student').all().order_by('-payment_date')
        
        if search:
            payments = payments.filter(
                Q(student__full_name__icontains=search) |
                Q(student__mobile_own__icontains=search) |
                Q(receipt_no__icontains=search)
            )
        
        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                payments = payments.filter(payment_date__date=filter_date)
            except ValueError:
                pass
        
        if month:
            try:
                payments = payments.filter(payment_date__month=int(month))
            except ValueError:
                pass
        
        if year:
            try:
                payments = payments.filter(payment_date__year=int(year))
            except ValueError:
                pass
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Payment Receipts"
        
        headers = [
            'Receipt No', 'Student Name', 'Mobile', 'Course', 
            'Payment Date', 'Payment Mode', 'Total Fees', 
            'Paid Before', 'Amount Paid', 'Remaining Fees', 'Remarks'
        ]
        
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=12)
        
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
        
        for row_num, payment in enumerate(payments, 2):
            course_name = payment.student.custom_course if payment.student.course == 'Other' and payment.student.custom_course else payment.student.course
            
            ws.cell(row=row_num, column=1).value = payment.receipt_no
            ws.cell(row=row_num, column=2).value = payment.student.full_name
            ws.cell(row=row_num, column=3).value = payment.student.mobile_own
            ws.cell(row=row_num, column=4).value = course_name
            ws.cell(row=row_num, column=5).value = payment.payment_date.strftime('%d-%m-%Y')
            ws.cell(row=row_num, column=6).value = payment.payment_mode
            ws.cell(row=row_num, column=7).value = float(payment.total_fees_at_payment)
            ws.cell(row=row_num, column=8).value = float(payment.paid_before_this)
            ws.cell(row=row_num, column=9).value = float(payment.amount)
            ws.cell(row=row_num, column=10).value = float(payment.remaining_after_this)
            ws.cell(row=row_num, column=11).value = payment.remarks or ''
        
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except (TypeError, AttributeError):
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        excel_file = BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)
        
        response = HttpResponse(
            excel_file.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        filename = f'receipts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ================= EXPORT ADMITTED STUDENTS TO EXCEL =================
@login_required
def export_admitted_students_excel(request):
    search = request.GET.get('search', '')
    month = request.GET.get('month', '')
    year = request.GET.get('year', '')
    course = request.GET.get('course', '')
    
    students = AdmittedStudent.objects.all()
    
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
    
    students = students.order_by('-admission_date')
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Admitted Students"
    
    headers = [
        'S.No', 'Full Name', 'Student Name', 'Father Name', 'Surname', 'Mother Name',
        'Date of Birth', 'Mobile (Own)', 'Parent Mobile', 'Gender', 'Marital Status',
        'Course', 'Batch Month', 'Batch Year', 'Educational Qualification',
        'Address', 'City', 'Tehsil/Block', 'District', 'Pin Code',
        'Total Fees (₹)', 'Paid Fees First Installment', 'Admission Date'
    ]
    
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=12)
    
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    for row_num, student in enumerate(students, 2):
        ws.cell(row=row_num, column=1).value = row_num - 1
        ws.cell(row=row_num, column=2).value = student.full_name
        ws.cell(row=row_num, column=3).value = student.student_name
        ws.cell(row=row_num, column=4).value = student.father_name
        ws.cell(row=row_num, column=5).value = student.surname
        ws.cell(row=row_num, column=6).value = student.mother_name
        ws.cell(row=row_num, column=7).value = student.date_of_birth.strftime('%d-%m-%Y') if student.date_of_birth else ''
        ws.cell(row=row_num, column=8).value = student.mobile_own
        ws.cell(row=row_num, column=9).value = student.parent_mobile or ''
        ws.cell(row=row_num, column=10).value = student.gender
        ws.cell(row=row_num, column=11).value = student.marital_status
        ws.cell(row=row_num, column=12).value = student.course
        ws.cell(row=row_num, column=13).value = student.batch_month or ''
        ws.cell(row=row_num, column=14).value = student.batch_year or ''
        ws.cell(row=row_num, column=15).value = student.educational_qualification
        ws.cell(row=row_num, column=16).value = student.address
        ws.cell(row=row_num, column=17).value = student.city
        ws.cell(row=row_num, column=18).value = student.tehsil_block
        ws.cell(row=row_num, column=19).value = student.district
        ws.cell(row=row_num, column=20).value = student.pin_code
        ws.cell(row=row_num, column=21).value = float(student.total_fees)
        ws.cell(row=row_num, column=22).value = float(student.paid_fees) if student.paid_fees else 0
        ws.cell(row=row_num, column=23).value = student.admission_date.strftime('%d-%m-%Y')
    
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except (TypeError, AttributeError):
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    excel_file = BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)
    
    response = HttpResponse(
        excel_file.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    filename_parts = ['admitted_students']
    if search:
        filename_parts.append(f'search_{search[:20]}')
    if course:
        filename_parts.append(f'{course}')
    if month:
        filename_parts.append(f'month_{month}')
    if year:
        filename_parts.append(f'{year}')
    filename_parts.append(datetime.now().strftime("%Y%m%d_%H%M%S"))
    
    filename = '_'.join(filename_parts) + '.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


# ================= DELETE ADMITTED STUDENTS =================
@login_required
@staff_member_required
@require_http_methods(["POST"])
def delete_admitted_students(request):
    """Delete multiple admitted students at once"""
    try:
        data = json.loads(request.body)
        student_ids = data.get('student_ids', [])
        
        if not student_ids:
            return JsonResponse({
                'success': False,
                'error': 'No students selected'
            })
        
        try:
            student_ids = [int(id) for id in student_ids]
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'Invalid student IDs'
            })
        
        students_to_delete = AdmittedStudent.objects.filter(id__in=student_ids)
        
        if not students_to_delete.exists():
            return JsonResponse({
                'success': False,
                'error': 'No students found with the given IDs'
            })
        
        delete_count = students_to_delete.count()
        
        try:
            from django.db import connection
            
            # For SQLite, disable foreign key constraints BEFORE the transaction
            fk_disabled = False
            if connection.settings_dict['ENGINE'] == 'django.db.backends.sqlite3':
                cursor = connection.cursor()
                cursor.execute('PRAGMA foreign_keys = OFF;')
                connection.commit()
                fk_disabled = True
            
            try:
                with transaction.atomic():
                    # Delete related records in proper order
                    for student in students_to_delete:
                        try:
                            # Delete fee payments
                            FeePayment.objects.filter(student=student).delete()
                            
                            # Delete attendance records
                            Attendance.objects.filter(student=student).delete()
                            
                            # Delete finance details
                            StudentFinanceDetail.objects.filter(student=student).delete()
                            
                            # Delete photo file if exists
                            if student.photo:
                                try:
                                    if student.photo.path:
                                        if os.path.isfile(student.photo.path):
                                            os.remove(student.photo.path)
                                except Exception as e:
                                    print(f"Error deleting photo for student {student.id}: {str(e)}")
                            
                            # Finally delete the student
                            student.delete()
                        except Exception as e:
                            print(f"Error deleting student {student.id}: {str(e)}")
                            continue
            finally:
                # Re-enable foreign key constraints for SQLite
                if fk_disabled:
                    cursor = connection.cursor()
                    cursor.execute('PRAGMA foreign_keys = ON;')
                    connection.commit()
                    
        except Exception as e:
            print(f"Error in delete transaction: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Error deleting students: {str(e)}'
            }, status=500)
        
        return JsonResponse({
            'success': True,
            'deleted_count': delete_count,
            'message': f'Successfully deleted {delete_count} student(s)'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        print(f"Delete error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


# ================= DATABASE BACKUP =================
@login_required
def backup_page(request):
    """Display the backup and restore page"""
    context = {
        'active_page': 'backup',
    }
    return render(request, 'core/backup.html', context)


@login_required
def export_database(request):
    """Export database as SQLite file with photos"""
    try:
        import zipfile
        import tempfile
        from io import BytesIO
        
        db_path = settings.DATABASES['default']['NAME']
        
        # Convert Path object to string
        db_path = str(db_path)
        
        # Check if file exists
        if not os.path.exists(db_path):
            return JsonResponse({'success': False, 'error': 'Database file not found'}, status=500)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'ssc_education_backup_{timestamp}.zip'
        
        # Create a ZIP file in memory
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add database file to ZIP
            db_filename = os.path.basename(db_path)
            zip_file.write(db_path, arcname=f'database/{db_filename}')
            
            # Add student photos if they exist
            media_path = os.path.join(settings.BASE_DIR, 'media', 'student_photos')
            if os.path.exists(media_path):
                for root, dirs, files in os.walk(media_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Calculate relative path for ZIP
                        relative_path = os.path.relpath(file_path, settings.BASE_DIR)
                        zip_file.write(file_path, arcname=relative_path)
        
        # Prepare response
        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{backup_name}"'
        
        return response
    
    except Exception as e:
        print(f"Export database error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def import_database(request):
    """Import database and photos from backup ZIP file (merge/update instead of overwrite)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)
    
    if 'database_file' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'No file provided'}, status=400)
    
    uploaded_file = request.FILES['database_file']
    
    # Validate file - now accepts ZIP or raw database files
    valid_extensions = ['db', 'sqlite', 'sqlite3', 'zip']
    file_extension = uploaded_file.name.split('.')[-1].lower()
    
    if file_extension not in valid_extensions:
        return JsonResponse({'success': False, 'error': 'Invalid file type. Only .db, .sqlite, .sqlite3, or .zip files are allowed.'}, status=400)
    
    max_size = 500 * 1024 * 1024  # 500 MB for ZIP files with photos
    if uploaded_file.size > max_size:
        return JsonResponse({'success': False, 'error': 'File too large. Maximum size is 500 MB.'}, status=400)
    
    try:
        import sqlite3
        import tempfile
        import zipfile
        
        db_path = settings.DATABASES['default']['NAME']
        
        # Create backup of current database before importing
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'database_backup_before_import_{timestamp}.db'
        backup_path = os.path.join(settings.BASE_DIR, backup_name)
        shutil.copy2(db_path, backup_path)
        
        # Create backup of current photos before importing
        photos_backup_path = None
        media_path = os.path.join(settings.BASE_DIR, 'media', 'student_photos')
        if os.path.exists(media_path):
            photos_backup_dir = os.path.join(settings.BASE_DIR, f'student_photos_backup_{timestamp}')
            shutil.copytree(media_path, photos_backup_dir)
            photos_backup_path = photos_backup_dir
        
        temp_db_path = None
        temp_dir = None
        
        try:
            # Check if uploaded file is a ZIP file
            if file_extension == 'zip':
                # Extract ZIP file
                temp_dir = tempfile.mkdtemp()
                with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Find database file in extracted ZIP
                temp_db_path = None
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file.endswith(('.db', '.sqlite', '.sqlite3')):
                            temp_db_path = os.path.join(root, file)
                            break
                    if temp_db_path:
                        break
                
                if not temp_db_path:
                    return JsonResponse({'success': False, 'error': 'No database file found in backup ZIP'}, status=400)
                
                # Extract and restore student photos if they exist in ZIP
                photos_count = 0
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if 'student_photos' in root:
                            src_file = os.path.join(root, file)
                            # Calculate destination path
                            rel_path = os.path.relpath(src_file, temp_dir)
                            dst_file = os.path.join(settings.BASE_DIR, rel_path)
                            
                            # Create directory if needed
                            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                            
                            # Copy file
                            shutil.copy2(src_file, dst_file)
                            photos_count += 1
            else:
                # Handle raw database file upload
                with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    temp_db_path = tmp_file.name
            
            # Merge data from imported database into current database
            current_conn = sqlite3.connect(db_path)
            imported_conn = sqlite3.connect(temp_db_path)
            
            imported_cursor = imported_conn.cursor()
            current_cursor = current_conn.cursor()
            
            # Get all table names from imported database
            imported_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = imported_cursor.fetchall()
            
            merged_count = 0
            skipped_count = 0
            
            # Merge each table's data
            for (table_name,) in tables:
                try:
                    # Get columns for the table
                    imported_cursor.execute(f"PRAGMA table_info({table_name})")
                    columns_info = imported_cursor.fetchall()
                    columns = [col[1] for col in columns_info]
                    primary_keys = [col[1] for col in columns_info if col[5]]  # col[5] is pk flag
                    
                    # Get all records from imported table
                    imported_cursor.execute(f"SELECT * FROM {table_name}")
                    rows = imported_cursor.fetchall()
                    
                    # Insert or update records in current database
                    for row in rows:
                        row_dict = dict(zip(columns, row))
                        
                        # Check if record exists (for tables with primary keys)
                        if primary_keys:
                            pk_column = primary_keys[0]
                            current_cursor.execute(
                                f"SELECT 1 FROM {table_name} WHERE {pk_column} = ?",
                                (row_dict[pk_column],)
                            )
                            record_exists = current_cursor.fetchone() is not None
                            
                            if record_exists:
                                # Update existing record
                                set_clause = ', '.join([f"{col} = ?" for col in columns if col != pk_column])
                                values = [row_dict[col] for col in columns if col != pk_column]
                                values.append(row_dict[pk_column])
                                
                                current_cursor.execute(
                                    f"UPDATE {table_name} SET {set_clause} WHERE {pk_column} = ?",
                                    values
                                )
                                merged_count += 1
                            else:
                                # Insert new record
                                placeholders = ', '.join(['?' for _ in columns])
                                current_cursor.execute(
                                    f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})",
                                    tuple(row)
                                )
                                merged_count += 1
                        else:
                            # If no primary key, just insert
                            placeholders = ', '.join(['?' for _ in columns])
                            current_cursor.execute(
                                f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})",
                                tuple(row)
                            )
                            merged_count += 1
                
                except Exception as table_error:
                    print(f"Error merging table {table_name}: {str(table_error)}")
                    skipped_count += 1
                    continue
            
            # Commit changes and close connections
            current_conn.commit()
            current_conn.close()
            imported_conn.close()
            
            # Prepare success message
            message = f'Database updated successfully! {merged_count} records merged/updated. Backup saved as {backup_name}'
            if file_extension == 'zip':
                message += f'. Student photos restored.'
            
            return JsonResponse({
                'success': True,
                'message': message
            })
        
        finally:
            # Clean up temporary files
            if temp_db_path and os.path.exists(temp_db_path):
                os.remove(temp_db_path)
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    except Exception as e:
        print(f"Import error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': f'Error importing database: {str(e)}'}, status=500)
    

@login_required
def statistics_view(request):
    """Main statistics page with year selection"""
    selected_year = request.GET.get('year', '')
    
    # Get available years from AdmittedStudent
    available_years = (
        AdmittedStudent.objects
        .annotate(year=ExtractYear('admission_date'))
        .values_list('year', flat=True)
        .distinct()
        .order_by('-year')
    )
    
    # Get students for selected year
    students = AdmittedStudent.objects.all()
    if selected_year:
        students = students.filter(admission_date__year=selected_year)
    
    # Helper function to calculate total profit
    def calculate_total_profit(student_queryset):
        total = Decimal('0.00')
        for student in student_queryset:
            # Get or create finance detail record
            finance_detail, created = StudentFinanceDetail.objects.get_or_create(
                student=student,
                defaults={
                    'first_installment': Decimal('0.00'),
                    'second_installment': Decimal('0.00'),
                    'third_installment': Decimal('0.00'),
                    'fourth_installment': Decimal('0.00'),
                    'fifth_installment': Decimal('0.00'),
                    'fees_paid_to_mkcl_1': Decimal('0.00'),
                    'fees_paid_to_mkcl_2': Decimal('0.00'),
                }
            )
            
            # Calculate fees paid to MKCL - default to 0
            mkcl_1 = finance_detail.fees_paid_to_mkcl_1 or Decimal('0.00')
            mkcl_2 = finance_detail.fees_paid_to_mkcl_2 or Decimal('0.00')
            
            mkcl_total = mkcl_1 + mkcl_2
            
            # Get fee payments for this student - ordered by payment_date (oldest first)
            fee_payments = FeePayment.objects.filter(student=student).order_by('payment_date')
            
            # Extract installment amounts from FeePayment records (5 installments)
            first_inst = Decimal('0.00')
            second_inst = Decimal('0.00')
            third_inst = Decimal('0.00')
            fourth_inst = Decimal('0.00')
            fifth_inst = Decimal('0.00')
            
            if len(fee_payments) >= 1:
                first_inst = fee_payments[0].amount
            if len(fee_payments) >= 2:
                second_inst = fee_payments[1].amount
            if len(fee_payments) >= 3:
                third_inst = fee_payments[2].amount
            if len(fee_payments) >= 4:
                fourth_inst = fee_payments[3].amount
            if len(fee_payments) >= 5:
                fifth_inst = fee_payments[4].amount
            
            # Calculate profit as (Total Fees Paid By Learner) - (Total Fees Paid to MKCL)
            learner_total_paid = first_inst + second_inst + third_inst + fourth_inst + fifth_inst
            profit = learner_total_paid - mkcl_total
            total += profit
        
        return total
    
    # Calculate total profit for selected year (or current year if no selection)
    total_profit = calculate_total_profit(students)
    
    # Calculate total profit for all years
    all_students = AdmittedStudent.objects.all()
    total_profit_all_years = calculate_total_profit(all_students)
    
    # Get current year
    current_year = datetime.now().year
    current_year_students = AdmittedStudent.objects.filter(admission_date__year=current_year)
    total_profit_current_year = calculate_total_profit(current_year_students)
    
    context = {
        'available_years': available_years,
        'selected_year': selected_year,
        'total_profit': total_profit,
        'total_profit_current_year': total_profit_current_year,
        'total_profit_all_years': total_profit_all_years,
        'current_year': current_year,
        'total_admitted': students.count(),
        'student_count': students.count(),
    }
    return render(request, 'core/statistics.html', context)


@login_required
@login_required
def student_finance_details(request):
    """Student Finance Details section with filtering and sorting"""
    selected_year = request.GET.get('year', '')
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', 'name')  # default sort by name
    course_filter = request.GET.get('course', '')
    batch_filter = request.GET.get('batch', '')
    
    # Get available years from AdmittedStudent
    available_years = (
        AdmittedStudent.objects
        .annotate(year=ExtractYear('admission_date'))
        .values_list('year', flat=True)
        .distinct()
        .order_by('-year')
    )
    
    # Get all available courses
    available_courses = (
        AdmittedStudent.objects
        .values_list('course', flat=True)
        .distinct()
        .order_by('course')
    )
    
    # Get all available batches
    available_batches = (
        AdmittedStudent.objects
        .values_list('batch_month', 'batch_year')
        .distinct()
        .order_by('-batch_year', '-batch_month')
    )
    # Format batches as "Month Year"
    formatted_batches = []
    for month, year in available_batches:
        if month and year:
            formatted_batches.append(f"{month} {year}")
    
    # Get all admitted students with filters
    students = AdmittedStudent.objects.all()
    
    # Apply year filter
    if selected_year:
        students = students.filter(admission_date__year=selected_year)
    
    # Apply course filter
    if course_filter:
        students = students.filter(course=course_filter)
    
    # Apply batch filter
    if batch_filter:
        batch_parts = batch_filter.split()
        if len(batch_parts) >= 2:
            month = ' '.join(batch_parts[:-1])  # All but last part
            year = batch_parts[-1]  # Last part
            students = students.filter(batch_month=month, batch_year=year)
    
    # Apply search filter (search by name or mobile)
    if search_query:
        students = students.filter(
            Q(full_name__icontains=search_query) |
            Q(student_name__icontains=search_query) |
            Q(mobile_own__icontains=search_query)
        )
    
    finance_data = []
    total_profit = Decimal('0.00')
    
    for student in students:
        # Get or create finance detail record
        finance_detail, created = StudentFinanceDetail.objects.get_or_create(
            student=student,
            defaults={
                'first_installment': Decimal('0.00'),
                'second_installment': Decimal('0.00'),
                'third_installment': Decimal('0.00'),
                'fourth_installment': Decimal('0.00'),
                'fifth_installment': Decimal('0.00'),
                'fees_paid_to_mkcl_1': Decimal('0.00'),
                'fees_paid_to_mkcl_2': Decimal('0.00'),
            }
        )
        
        # Calculate totals from AdmittedStudent
        total_paid = student.paid_fees or Decimal('0.00')
        total_fees = student.total_fees or Decimal('0.00')
        balance_fees = total_fees - total_paid
        
        # Get course name for defaults logic
        course_name = student.custom_course if student.course == 'Other' and student.custom_course else student.course
        
        # Calculate fees paid to MKCL - default to 0
        mkcl_1 = finance_detail.fees_paid_to_mkcl_1 or Decimal('0.00')
        mkcl_2 = finance_detail.fees_paid_to_mkcl_2 or Decimal('0.00')
        
        mkcl_total = mkcl_1 + mkcl_2
        
        # Get fee payments for this student - ordered by payment_date (oldest first)
        fee_payments = FeePayment.objects.filter(student=student).order_by('payment_date')
        
        # Extract installment amounts from FeePayment records (5 installments)
        first_inst = Decimal('0.00')
        second_inst = Decimal('0.00')
        third_inst = Decimal('0.00')
        fourth_inst = Decimal('0.00')
        fifth_inst = Decimal('0.00')
        
        if len(fee_payments) >= 1:
            first_inst = fee_payments[0].amount
        if len(fee_payments) >= 2:
            second_inst = fee_payments[1].amount
        if len(fee_payments) >= 3:
            third_inst = fee_payments[2].amount
        if len(fee_payments) >= 4:
            fourth_inst = fee_payments[3].amount
        if len(fee_payments) >= 5:
            fifth_inst = fee_payments[4].amount
        
        # Calculate profit as (Total Fees Paid By Learner) - (Total Fees Paid to MKCL)
        learner_total_paid = first_inst + second_inst + third_inst + fourth_inst + fifth_inst
        profit = learner_total_paid - mkcl_total
        total_profit += profit
        
        # Build payment history (ordered by payment_date, newest first for display)
        payment_history = []
        for payment in fee_payments.order_by('-payment_date'):
            payment_history.append({
                'receipt_no': payment.receipt_no,
                'amount': payment.amount,
                'payment_date': payment.payment_date,
                'payment_mode': payment.payment_mode,
                'remarks': payment.remarks,
                'paid_before': payment.paid_before_this,
                'remaining_after': payment.remaining_after_this,
            })
        
        finance_data.append({
            'id': student.id,
            'sr_no': student.id,
            'learner_name': student.full_name or f"{student.student_name} {student.father_name} {student.surname}",
            'student_id': student.id,  # Using student ID as identifier
            'mobile_no': student.mobile_own,
            'batch': student.batch_display,
            'course': course_name,
            'first_inst': first_inst,
            'second_inst': second_inst,
            'third_inst': third_inst,
            'fourth_inst': fourth_inst,
            'fifth_inst': fifth_inst,
            'total_paid': total_paid,
            'total_fees': total_fees,
            'balance_fees': balance_fees,
            'mkcl_1': mkcl_1,
            'mkcl_2': mkcl_2,
            'mkcl_total': mkcl_total,
            'profit': profit,
            'payment_history': payment_history,
        })
    
    # Apply sorting
    if sort_by == 'name':
        finance_data.sort(key=lambda x: x['learner_name'])
    elif sort_by == 'mobile':
        finance_data.sort(key=lambda x: x['mobile_no'] or '')
    elif sort_by == 'course':
        finance_data.sort(key=lambda x: x['course'])
    elif sort_by == 'batch':
        finance_data.sort(key=lambda x: x['batch'])
    elif sort_by == 'total_paid':
        finance_data.sort(key=lambda x: float(x['total_paid'] or 0), reverse=True)
    elif sort_by == 'balance':
        finance_data.sort(key=lambda x: float(x['balance_fees'] or 0), reverse=True)
    elif sort_by == 'profit':
        finance_data.sort(key=lambda x: float(x['profit'] or 0), reverse=True)
    
    context = {
        'finance_data': finance_data,
        'total_profit': total_profit,
        'selected_year': selected_year,
        'available_years': available_years,
        'available_courses': available_courses,
        'available_batches': formatted_batches,
        'search_query': search_query,
        'course_filter': course_filter,
        'batch_filter': batch_filter,
        'sort_by': sort_by,
        'active_page': 'student_finance_details',
    }
    
    return render(request, 'core/student_finance_details.html', context)

@login_required
def update_finance_detail(request):
    """AJAX endpoint to update finance details"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            student_id = data.get('student_id')
            field = data.get('field')
            value = data.get('value', '0')
            
            # Convert value to Decimal
            try:
                value = Decimal(value) if value else Decimal('0.00')
            except:
                value = Decimal('0.00')
            
            student = AdmittedStudent.objects.get(id=student_id)
            finance_detail, created = StudentFinanceDetail.objects.get_or_create(student=student)
            
            # Only allow updates to MKCL fees (learner fees are read-only based on FeePayment records)
            if field == 'mkcl_1':
                finance_detail.fees_paid_to_mkcl_1 = value
            elif field == 'mkcl_2':
                finance_detail.fees_paid_to_mkcl_2 = value
            else:
                # Reject attempts to update learner fees (first_inst, second_inst, third_inst)
                return JsonResponse({'success': False, 'error': 'Cannot update learner fees. These are based on actual payment records.'})
            
            finance_detail.save()
            
            # Recalculate totals
            total_paid = student.paid_fees or Decimal('0.00')
            mkcl_total = (finance_detail.fees_paid_to_mkcl_1 or Decimal('0.00')) + \
                        (finance_detail.fees_paid_to_mkcl_2 or Decimal('0.00'))
            profit = total_paid - mkcl_total
            
            return JsonResponse({
                'success': True,
                'mkcl_total': float(mkcl_total),
                'profit': float(profit)
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def month_wise_admission(request):
    """Month wise admission details view"""
    from datetime import datetime
    
    current_year = datetime.now().year
    selected_year = request.GET.get('year', str(current_year))  # Default to current year
    
    # Get all years for filter
    years = AdmittedStudent.objects.dates('admission_date', 'year', order='DESC')
    available_years = [date.year for date in years]
    
    # Get admitted students
    students = AdmittedStudent.objects.all()
    if selected_year:
        students = students.filter(admission_date__year=int(selected_year))
    
    # Get all unique courses dynamically from AdmittedStudent records
    courses_qs = students.values_list('course', flat=True).distinct()
    # Add custom courses if they exist
    custom_courses_qs = students.values_list('custom_course', flat=True).distinct()
    
    # Combine and clean - remove None and empty strings
    all_courses = set(courses_qs) | set(custom_courses_qs)
    all_courses.discard(None)
    all_courses.discard('')
    all_courses = sorted(list(all_courses))
    
    months = ['jan', 'feb', 'march', 'april', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    
    # Initialize data structure
    monthly_admission_data = []
    monthly_totals = {month: 0 for month in months}
    grand_total = 0
    
    # Count admissions by course and month
    for course in all_courses:
        course_data = {'course': course}
        course_total = 0
        
        for month_num, month_key in enumerate(months, 1):
            count = students.filter(
                admission_date__month=month_num
            ).filter(
                Q(course=course) | Q(custom_course=course)
            ).count()
            
            course_data[month_key] = count if count > 0 else '-'
            if count > 0:
                monthly_totals[month_key] += count
                course_total += count
        
        course_data['total'] = course_total if course_total > 0 else '-'
        monthly_admission_data.append(course_data)
        grand_total += course_total
    
    # Convert monthly_totals zeros to '-'
    for month_key in months:
        if monthly_totals[month_key] == 0:
            monthly_totals[month_key] = '-'
    
    # Calculate monthly profit data by course using StudentFinanceDetail
    # This takes the total profit from each student's finance detail and adds it up by course and admission month
    monthly_profit_data = []
    profit_monthly_totals = {month: Decimal('0.00') for month in months}
    profit_grand_total = Decimal('0.00')
    
    for course in all_courses:
        course_profit = {'course': course}
        course_profit_total = Decimal('0.00')
        
        for month_num, month_key in enumerate(months, 1):
            # Get all students for this course admitted in this month
            course_students = students.filter(
                admission_date__month=month_num,
                admission_date__year=int(selected_year) if selected_year else datetime.now().year
            ).filter(
                Q(course=course) | Q(custom_course=course)
            )
            
            # Sum the profit from StudentFinanceDetail for these students
            month_profit = Decimal('0.00')
            
            for student in course_students:
                # Get the finance detail for this student
                try:
                    finance_detail = StudentFinanceDetail.objects.get(student=student)
                    # Use the profit property which calculates: paid_fees - total_mkcl_fees
                    student_profit = Decimal(str(finance_detail.profit or 0))
                    month_profit += student_profit
                except StudentFinanceDetail.DoesNotExist:
                    # If no finance detail exists, calculate it manually
                    pass
            
            # Format and store
            if month_profit > 0:
                course_profit[month_key] = f"₹ {month_profit:.2f}"
                profit_monthly_totals[month_key] += month_profit
                course_profit_total += month_profit
            else:
                course_profit[month_key] = '-'
        
        course_profit['total'] = f"₹ {course_profit_total:.2f}" if course_profit_total > 0 else '-'
        monthly_profit_data.append(course_profit)
        profit_grand_total += course_profit_total
    
    # Format monthly profit totals
    monthly_profit_totals_formatted = {}
    for month_key in months:
        if profit_monthly_totals[month_key] > 0:
            monthly_profit_totals_formatted[month_key] = f"₹ {profit_monthly_totals[month_key]:.2f}"
        else:
            monthly_profit_totals_formatted[month_key] = '-'
    
    context = {
        'monthly_admission_data': monthly_admission_data,
        'monthly_totals': monthly_totals,
        'grand_total': grand_total if grand_total > 0 else '-',
        'monthly_profit_data': monthly_profit_data,
        'monthly_profit_totals': monthly_profit_totals_formatted,
        'profit_grand_total': f"₹ {profit_grand_total:.2f}" if profit_grand_total > 0 else '₹ 0.00',
        'selected_year': selected_year or str(datetime.now().year),
        'available_years': available_years,
        'active_page': 'month_wise_admission',
    }
    
    return render(request, 'core/month_wise_admission.html', context)


# ================= SALES AND SERVICES VIEWS =================

@login_required
def sales_services_dashboard(request):
    """Sales and Services Dashboard"""
    context = {
        'active_page': 'sales_dashboard',
    }
    return render(request, 'core/sales_dashboard.html', context)


@login_required
def sales_items(request):
    """Sales Items Management"""
    items = SalesItem.objects.all()
    context = {
        'active_page': 'sales_items',
        'items': items,
    }
    return render(request, 'core/sales_items.html', context)


@login_required
def add_sales_item(request):
    """Add new sales item"""
    if request.method == 'POST':
        item_name = request.POST.get('item_name')
        quantity = request.POST.get('quantity')
        purchase_rate = request.POST.get('purchase_rate')
        purchased_from = request.POST.get('purchased_from')
        total_amount = request.POST.get('total_amount')
        
        
        try:
            SalesItem.objects.create(
                item_name=item_name,
                quantity=int(quantity),
                purchase_rate=Decimal(purchase_rate),
                purchased_from=purchased_from,
                total_amount=Decimal(total_amount)
            )
            messages.success(request, f"Item '{item_name}' added successfully!")
        except Exception as e:
            messages.error(request, f"Error adding item: {str(e)}")
        
        return redirect('sales_items')
    
    return redirect('sales_items')


# ================= PAYMENT TRACKING PAGE =================
@login_required(login_url='login')
def payment_tracking(request):
    """Show students whose 1st installment was paid before X days"""
    from datetime import date, timedelta
    
    # Get number of days from request, default to 25
    days = request.GET.get('days', '25')
    try:
        days = int(days)
        if days < 1:
            days = 25
    except (ValueError, TypeError):
        days = 25
    
    # Get date X days ago
    cutoff_date = date.today() - timedelta(days=days)
    
    # Get all students who have at least one payment
    students_with_payments = AdmittedStudent.objects.filter(
        fee_payments__isnull=False
    ).distinct()
    
    # Filter students where the earliest (1st) payment was before 25 days
    eligible_students = []
    for student in students_with_payments:
        all_payments = student.fee_payments.all()
        if not all_payments.exists():
            continue
            
        first_payment = all_payments.order_by('payment_date').first()
        if not first_payment or not first_payment.payment_date:
            continue
            
        if first_payment.payment_date <= cutoff_date:
            # Get payment summary
            total_paid = all_payments.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
            total_fees = student.total_fees or Decimal('0')
            remaining = total_fees - total_paid
            
            # Only include students with remaining fees to pay
            if remaining > 0:
                last_payment = all_payments.order_by('-payment_date').first()
                last_payment_date = last_payment.payment_date if last_payment and last_payment.payment_date else None
                
                eligible_students.append({
                    'student': student,
                    'first_payment_date': first_payment.payment_date,
                    'total_paid': total_paid,
                    'total_fees': total_fees,
                    'remaining': remaining,
                    'payment_count': all_payments.count(),
                    'last_payment_date': last_payment_date,
                })
    
    # Sort by first payment date
    eligible_students = sorted(eligible_students, key=lambda x: x['first_payment_date'])
    
    # Pagination
    paginator = Paginator(eligible_students, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'eligible_students': page_obj.object_list,
        'total_count': len(eligible_students),
        'days': days,
        'cutoff_date': cutoff_date,
        'active_page': 'payment_tracking',
    }
    
    return render(request, 'core/payment_tracking.html', context)


@login_required(login_url='login')
def payment_tracking_student_detail(request, student_id):
    """Get student details for modal display in payment tracking"""
    student = get_object_or_404(AdmittedStudent, id=student_id)
    
    # Get payment summary
    all_payments = student.fee_payments.all()
    total_paid = all_payments.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    total_fees = student.total_fees or Decimal('0')
    remaining = total_fees - total_paid
    
    # Get payment history
    payments = all_payments.order_by('-payment_date').values(
        'receipt_no', 'amount', 'payment_date', 'payment_mode'
    )
    
    data = {
        'id': student.id,
        'full_name': student.full_name,
        'student_name': student.student_name,
        'father_name': student.father_name,
        'mother_name': student.mother_name,
        'date_of_birth': str(student.date_of_birth) if student.date_of_birth else '',
        'gender': student.gender,
        'marital_status': student.marital_status,
        'mobile_own': student.mobile_own,
        'parent_mobile': student.parent_mobile,
        'address': student.address or '',
        'city': student.city or '',
        'tehsil_block': student.tehsil_block or '',
        'district': student.district or '',
        'pin_code': student.pin_code or '',
        'educational_qualification': student.educational_qualification or '',
        'course': student.course or '',
        'batch_month': student.batch_month or '',
        'batch_year': student.batch_year or '',
        'admission_date': str(student.admission_date) if student.admission_date else '',
        'photo': student.photo.url if student.photo else '',
        'total_fees': str(total_fees),
        'total_paid': str(total_paid),
        'remaining': str(remaining),
        'payment_count': all_payments.count(),
        'payments': list(payments),
    }
    
    return JsonResponse(data)


# ================= ATTENDANCE MANAGEMENT SYSTEM =================

@login_required
def attendance_management(request):
    """Attendance management has been removed"""
    from django.http import HttpResponse
    return HttpResponse("Attendance management feature has been removed from this application.", status=410)


@login_required
def get_attendance_stats(request):
    """Feature removed"""
    return JsonResponse({'error': 'Attendance management feature has been removed'}, status=410)


@login_required
def get_daily_attendance_students(request):
    """Feature removed"""
    return JsonResponse({'error': 'Attendance management feature has been removed'}, status=410)


@login_required
def save_daily_attendance(request):
    """Feature removed"""
    return JsonResponse({'error': 'Attendance management feature has been removed'}, status=410)


@login_required
def get_monthly_timetable(request):
    """Feature removed"""
    return JsonResponse({'error': 'Attendance management feature has been removed'}, status=410)


@login_required
def get_monthly_report(request):
    """Feature removed"""
    return JsonResponse({'error': 'Attendance management feature has been removed'}, status=410)


@login_required
def export_attendance_excel(request):
    """Feature removed"""
    return JsonResponse({'error': 'Attendance management feature has been removed'}, status=410)


@login_required
def export_attendance_pdf(request):
    """Feature removed"""
    return JsonResponse({'error': 'Attendance management feature has been removed'}, status=410)


# ============= TIMETABLE & ATTENDANCE MANAGEMENT =============

@login_required
@staff_member_required
def student_timetable(request):
    """Display student timetable with batch assignments"""
    search_query = request.GET.get('search', '').strip()
    course_filter = request.GET.get('course', '')
    batch_month_filter = request.GET.get('batch_month', '')
    batch_year_filter = request.GET.get('batch_year', '')
    theory_batch_filter = request.GET.get('theory_batch', '')
    practical_batch_filter = request.GET.get('practical_batch', '')
    gender_filter = request.GET.get('gender', '')
    
    # Get all students with batch assignments
    students = AdmittedStudent.objects.all()
    
    # Apply search filter
    if search_query:
        students = students.filter(
            Q(full_name__icontains=search_query) |
            Q(student_name__icontains=search_query) |
            Q(mobile_own__icontains=search_query)
        )
    
    # Apply course filter
    if course_filter:
        students = students.filter(course=course_filter)
    
    # Apply batch month filter
    if batch_month_filter:
        students = students.filter(batch_month=batch_month_filter)
    
    # Apply batch year filter
    if batch_year_filter:
        students = students.filter(batch_year=batch_year_filter)
    
    # Apply theory batch filter
    if theory_batch_filter:
        students = students.filter(theory_batch_time=theory_batch_filter)
    
    # Apply practical batch filter
    if practical_batch_filter:
        students = students.filter(practical_batch_time=practical_batch_filter)
    
    # Apply gender filter
    if gender_filter:
        students = students.filter(gender=gender_filter)
    
    # Paginate results
    paginator = Paginator(students, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get available courses from AdmittedStudent
    course_choices = [
        ('MS-CIT', 'MS-CIT'),
        ('Tally', 'Tally'),
        ('Advance Excel', 'Advance Excel'),
        ('IOT', 'IOT'),
        ('Scratch', 'Scratch'),
        ('Other', 'Other'),
    ]
    all_courses = course_choices
    
    # Get available batch months and years
    available_batch_months = (
        AdmittedStudent.objects
        .exclude(batch_month__isnull=True)
        .exclude(batch_month='')
        .values_list('batch_month', flat=True)
        .distinct()
        .order_by('batch_month')
    )
    
    available_batch_years = (
        AdmittedStudent.objects
        .exclude(batch_year__isnull=True)
        .exclude(batch_year='')
        .values_list('batch_year', flat=True)
        .distinct()
        .order_by('-batch_year')
    )
    
    # Get available batches
    available_theory_batches = Batch.objects.filter(
        batch_type='Theory',
        course__isnull=True
    ).values_list('time_slot', flat=True).distinct().order_by('time_slot')
    
    available_practical_batches = Batch.objects.filter(
        batch_type='Practical',
        course__isnull=True
    ).values_list('time_slot', flat=True).distinct().order_by('time_slot')
    
    # Calculate total unique available time slots
    all_available_slots = set(list(available_theory_batches) + list(available_practical_batches))
    total_available_slots = len(all_available_slots)
    
    # Map time slots to display format
    time_slot_display_map = {
        '08:00-09:00': '8:00 AM - 9:00 AM',
        '09:00-10:00': '9:00 AM - 10:00 AM',
        '10:00-11:00': '10:00 AM - 11:00 AM',
        '11:00-12:00': '11:00 AM - 12:00 PM',
        '12:00-13:00': '12:00 PM - 1:00 PM',
        '15:00-16:00': '3:00 PM - 4:00 PM',
        '16:00-17:00': '4:00 PM - 5:00 PM',
        '17:00-18:00': '5:00 PM - 6:00 PM',
        '18:00-19:00': '6:00 PM - 7:00 PM',
    }
    
    time_slots = [
        ('08:00-09:00', '8:00 AM - 9:00 AM'),
        ('09:00-10:00', '9:00 AM - 10:00 AM'),
        ('10:00-11:00', '10:00 AM - 11:00 AM'),
        ('11:00-12:00', '11:00 AM - 12:00 PM'),
        ('12:00-13:00', '12:00 PM - 1:00 PM'),
        ('15:00-16:00', '3:00 PM - 4:00 PM'),
        ('16:00-17:00', '4:00 PM - 5:00 PM'),
        ('17:00-18:00', '5:00 PM - 6:00 PM'),
        ('18:00-19:00', '6:00 PM - 7:00 PM'),
    ]
    
    context = {
        'page_obj': page_obj,
        'students': page_obj.object_list,
        'search_query': search_query,
        'course_filter': course_filter,
        'batch_month_filter': batch_month_filter,
        'batch_year_filter': batch_year_filter,
        'theory_batch_filter': theory_batch_filter,
        'practical_batch_filter': practical_batch_filter,
        'gender_filter': gender_filter,
        'all_courses': all_courses,
        'available_batch_months': available_batch_months,
        'available_batch_years': available_batch_years,
        'available_theory_batches': available_theory_batches,
        'available_practical_batches': available_practical_batches,
        'total_available_slots': total_available_slots,
        'time_slot_display_map': time_slot_display_map,
        'total_students': students.count(),
        'time_slots': time_slots,
        'active_page': 'student_timetable'
    }
    
    return render(request, 'core/timetable/student_timetable.html', context)


@login_required
@staff_member_required
def edit_student_batch(request, student_id):
    """Edit student's theory and practical batch assignments"""
    student = get_object_or_404(AdmittedStudent, id=student_id)
    
    if request.method == 'POST':
        theory_batch = request.POST.get('theory_batch_time', '').strip()
        practical_batch = request.POST.get('practical_batch_time', '').strip()
        
        # Update student batches
        if theory_batch:
            student.theory_batch_time = theory_batch
        if practical_batch:
            student.practical_batch_time = practical_batch
        
        student.save()
        messages.success(request, f"✅ Batch timing updated for {student.full_name}")
        return redirect('student_timetable')
    
    # Get only existing theory and practical batches
    theory_batches = Batch.objects.filter(batch_type='Theory', course__isnull=True).values_list('time_slot', flat=True)
    practical_batches = Batch.objects.filter(batch_type='Practical', course__isnull=True).values_list('time_slot', flat=True)
    
    time_slots = [
        ('08:00-09:00', '8:00 AM - 9:00 AM'),
        ('09:00-10:00', '9:00 AM - 10:00 AM'),
        ('10:00-11:00', '10:00 AM - 11:00 AM'),
        ('11:00-12:00', '11:00 AM - 12:00 PM'),
        ('12:00-13:00', '12:00 PM - 1:00 PM'),
        ('15:00-16:00', '3:00 PM - 4:00 PM'),
        ('16:00-17:00', '4:00 PM - 5:00 PM'),
        ('17:00-18:00', '5:00 PM - 6:00 PM'),
        ('18:00-19:00', '6:00 PM - 7:00 PM'),
    ]
    
    # Filter to only show existing batches
    available_theory_slots = [(slot, display) for slot, display in time_slots if slot in theory_batches]
    available_practical_slots = [(slot, display) for slot, display in time_slots if slot in practical_batches]
    
    context = {
        'student': student,
        'theory_batches': available_theory_slots,
        'practical_batches': available_practical_slots,
        'active_page': 'student_timetable'
    }
    
    return render(request, 'core/timetable/edit_batch.html', context)


@login_required
@staff_member_required
def batch_overview_dashboard(request):
    """Dashboard showing batch-wise student distribution"""
    from django.db.models import Count
    
    time_slots = [
        ('08:00-09:00', '8:00 AM - 9:00 AM'),
        ('09:00-10:00', '9:00 AM - 10:00 AM'),
        ('10:00-11:00', '10:00 AM - 11:00 AM'),
        ('11:00-12:00', '11:00 AM - 12:00 PM'),
        ('12:00-13:00', '12:00 PM - 1:00 PM'),
        ('15:00-16:00', '3:00 PM - 4:00 PM'),
        ('16:00-17:00', '4:00 PM - 5:00 PM'),
        ('17:00-18:00', '5:00 PM - 6:00 PM'),
        ('18:00-19:00', '6:00 PM - 7:00 PM'),
    ]
    
    # Get only existing theory batches from database
    theory_batches = []
    for batch in Batch.objects.filter(batch_type='Theory', course__isnull=True):
        count = AdmittedStudent.objects.filter(theory_batch_time=batch.time_slot).count()
        display = dict(time_slots).get(batch.time_slot, batch.time_slot)
        theory_batches.append({
            'id': batch.id,
            'slot': batch.time_slot,
            'display': display,
            'count': count,
            'capacity': batch.capacity
        })
    
    # Get only existing practical batches from database
    practical_batches = []
    for batch in Batch.objects.filter(batch_type='Practical', course__isnull=True):
        count = AdmittedStudent.objects.filter(practical_batch_time=batch.time_slot).count()
        display = dict(time_slots).get(batch.time_slot, batch.time_slot)
        practical_batches.append({
            'id': batch.id,
            'slot': batch.time_slot,
            'display': display,
            'count': count,
            'capacity': batch.capacity
        })
    
    # Total statistics
    total_students = AdmittedStudent.objects.count()
    students_with_theory = AdmittedStudent.objects.filter(theory_batch_time__isnull=False).exclude(theory_batch_time='').count()
    students_with_practical = AdmittedStudent.objects.filter(practical_batch_time__isnull=False).exclude(practical_batch_time='').count()
    
    context = {
        'theory_batches': theory_batches,
        'practical_batches': practical_batches,
        'total_students': total_students,
        'students_with_theory': students_with_theory,
        'students_with_practical': students_with_practical,
        'students_without_batch': total_students - max(students_with_theory, students_with_practical),
        'active_page': 'batch_overview'
    }
    
    return render(request, 'core/timetable/batch_overview.html', context)


@login_required
@staff_member_required
def mark_attendance_page(request):
    """Page to mark attendance for a specific batch and date"""
    from datetime import datetime, date as date_class
    
    if request.method == 'POST':
        attendance_date = request.POST.get('attendance_date')
        batch_time = request.POST.get('batch_time')
        batch_type = request.POST.get('batch_type')
        
        if not all([attendance_date, batch_time, batch_type]):
            messages.error(request, "❌ Please select date, batch time, and batch type")
            return redirect('mark_attendance')
        
        return redirect('save_attendance', date=attendance_date, batch_time=batch_time, batch_type=batch_type)
    
    # Get only existing theory batches
    theory_batches = Batch.objects.filter(
        batch_type='Theory',
        course__isnull=True
    ).values_list('time_slot', flat=True).distinct()
    
    # Get only existing practical batches
    practical_batches = Batch.objects.filter(
        batch_type='Practical',
        course__isnull=True
    ).values_list('time_slot', flat=True).distinct()
    
    # Map time slots to display format
    time_slot_display_map = {
        '08:00-09:00': '8:00 AM - 9:00 AM',
        '09:00-10:00': '9:00 AM - 10:00 AM',
        '10:00-11:00': '10:00 AM - 11:00 AM',
        '11:00-12:00': '11:00 AM - 12:00 PM',
        '12:00-13:00': '12:00 PM - 1:00 PM',
        '15:00-16:00': '3:00 PM - 4:00 PM',
        '16:00-17:00': '4:00 PM - 5:00 PM',
        '17:00-18:00': '5:00 PM - 6:00 PM',
        '18:00-19:00': '6:00 PM - 7:00 PM',
    }
    
    # Create filtered time slots for display
    theory_slots = [(slot, time_slot_display_map.get(slot, slot)) for slot in theory_batches]
    practical_slots = [(slot, time_slot_display_map.get(slot, slot)) for slot in practical_batches]
    
    context = {
        'theory_slots': theory_slots,
        'practical_slots': practical_slots,
        'today': date_class.today().isoformat(),
        'active_page': 'mark_attendance'
    }
    
    return render(request, 'core/timetable/mark_attendance.html', context)


@login_required
@staff_member_required
def save_attendance(request, date, batch_time, batch_type):
    """Save attendance for students in a specific batch"""
    from datetime import datetime as dt
    
    # Parse date
    try:
        attendance_date = dt.strptime(date, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        messages.error(request, "❌ Invalid date format")
        return redirect('mark_attendance')
    
    # Get students for the selected batch
    if batch_type == 'theory':
        students = AdmittedStudent.objects.filter(theory_batch_time=batch_time).order_by('full_name')
    else:  # practical
        students = AdmittedStudent.objects.filter(practical_batch_time=batch_time).order_by('full_name')
    
    if request.method == 'POST':
        with transaction.atomic():
            for student in students:
                # Get attendance status
                attendance_key = f'attendance_{student.id}'
                status = request.POST.get(attendance_key, 'A')
                remarks = request.POST.get(f'remarks_{student.id}', '').strip()
                
                # Create or update attendance record
                attendance, created = Attendance.objects.get_or_create(
                    student=student,
                    date=attendance_date,
                    defaults={'marked_by': request.user}
                )
                
                # Update attendance based on batch type
                if batch_type == 'theory':
                    attendance.theory_attendance = status
                else:
                    attendance.practical_attendance = status
                
                if remarks:
                    attendance.remarks = remarks
                
                attendance.marked_by = request.user
                attendance.save()
        
        messages.success(request, f"✅ Attendance saved for {batch_type.capitalize()} batch on {attendance_date}")
        return redirect('attendance_reports')
    
    # Display form to mark attendance
    time_slot_display_map = {
        '08:00-09:00': '8:00 AM - 9:00 AM',
        '09:00-10:00': '9:00 AM - 10:00 AM',
        '10:00-11:00': '10:00 AM - 11:00 AM',
        '11:00-12:00': '11:00 AM - 12:00 PM',
        '12:00-13:00': '12:00 PM - 1:00 PM',
        '15:00-16:00': '3:00 PM - 4:00 PM',
        '16:00-17:00': '4:00 PM - 5:00 PM',
        '17:00-18:00': '5:00 PM - 6:00 PM',
        '18:00-19:00': '6:00 PM - 7:00 PM',
    }
    
    # Get time slot display
    time_slot_display = time_slot_display_map.get(batch_time, batch_time)
    
    context = {
        'students': students,
        'attendance_date': attendance_date,
        'batch_time': batch_time,
        'time_slot_display': time_slot_display,
        'batch_type': batch_type,
        'status_choices': [('P', 'Present'), ('A', 'Absent'), ('L', 'Leave'), ('H', 'Holiday')],
        'active_page': 'mark_attendance'
    }
    
    return render(request, 'core/timetable/save_attendance.html', context)


@login_required
@staff_member_required
def attendance_reports(request):
    """Comprehensive attendance reports"""
    from datetime import datetime, date as date_class, timedelta
    
    report_type = request.GET.get('report_type', 'student')
    
    # Student Attendance Report
    if report_type == 'student':
        students = AdmittedStudent.objects.all().order_by('full_name')
        
        student_reports = []
        for student in students:
            total_records = student.attendance_records.count()
            present_count = student.attendance_records.filter(
                Q(theory_attendance='P') | Q(practical_attendance='P')
            ).count()
            absent_count = total_records - present_count
            
            if total_records > 0:
                percentage = (present_count / total_records) * 100
            else:
                percentage = 0
            
            student_reports.append({
                'student': student,
                'total': total_records,
                'present': present_count,
                'absent': absent_count,
                'percentage': round(percentage, 2)
            })
        
        context = {
            'report_type': 'student',
            'student_reports': student_reports,
            'title': 'Student Attendance Report'
        }
    
    # Daily Report
    elif report_type == 'daily':
        selected_date = request.GET.get('date')
        
        if selected_date:
            try:
                report_date = dt.strptime(selected_date, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                report_date = date_class.today()
        else:
            report_date = date_class.today()
        
        # Get all attendance records for the date
        attendance_records = Attendance.objects.filter(date=report_date).select_related('student')
        
        total_students = AdmittedStudent.objects.count()
        present_count = attendance_records.filter(Q(theory_attendance='P') | Q(practical_attendance='P')).count()
        absent_count = total_students - present_count
        
        context = {
            'report_type': 'daily',
            'report_date': report_date,
            'attendance_records': attendance_records,
            'total_students': total_students,
            'present_count': present_count,
            'absent_count': absent_count,
            'title': f'Daily Attendance Report - {report_date}'
        }
    
    # Batch Attendance Report
    else:  # batch
        selected_date = request.GET.get('date')
        
        if selected_date:
            try:
                report_date = dt.strptime(selected_date, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                report_date = date_class.today()
        else:
            report_date = date_class.today()
        
        time_slot_display_map = {
            '08:00-09:00': '8:00 AM - 9:00 AM',
            '09:00-10:00': '9:00 AM - 10:00 AM',
            '10:00-11:00': '10:00 AM - 11:00 AM',
            '11:00-12:00': '11:00 AM - 12:00 PM',
            '12:00-13:00': '12:00 PM - 1:00 PM',
            '15:00-16:00': '3:00 PM - 4:00 PM',
            '16:00-17:00': '4:00 PM - 5:00 PM',
            '17:00-18:00': '5:00 PM - 6:00 PM',
            '18:00-19:00': '6:00 PM - 7:00 PM',
        }
        
        # Get all existing theory and practical batch time slots
        theory_slots = Batch.objects.filter(
            batch_type='Theory',
            course__isnull=True
        ).values_list('time_slot', flat=True).distinct()
        
        practical_slots = Batch.objects.filter(
            batch_type='Practical',
            course__isnull=True
        ).values_list('time_slot', flat=True).distinct()
        
        # Combine all unique slots
        all_slots = sorted(set(theory_slots) | set(practical_slots))
        
        batch_reports = []
        for slot in all_slots:
            display = time_slot_display_map.get(slot, slot)
            
            # Theory batch
            theory_students = AdmittedStudent.objects.filter(theory_batch_time=slot)
            theory_present = Attendance.objects.filter(
                student__in=theory_students,
                date=report_date,
                theory_attendance='P'
            ).count()
            theory_absent = theory_students.count() - theory_present
            
            # Practical batch
            practical_students = AdmittedStudent.objects.filter(practical_batch_time=slot)
            practical_present = Attendance.objects.filter(
                student__in=practical_students,
                date=report_date,
                practical_attendance='P'
            ).count()
            practical_absent = practical_students.count() - practical_present
            
            batch_reports.append({
                'slot': slot,
                'display': display,
                'theory': {
                    'total': theory_students.count(),
                    'present': theory_present,
                    'absent': theory_absent
                },
                'practical': {
                    'total': practical_students.count(),
                    'present': practical_present,
                    'absent': practical_absent
                }
            })
        
        context = {
            'report_type': 'batch',
            'report_date': report_date,
            'batch_reports': batch_reports,
            'title': f'Batch Attendance Report - {report_date}',
            'active_page': 'attendance_reports'
        }
    
    return render(request, 'core/timetable/attendance_reports.html', context)


@login_required
@staff_member_required
def export_timetable_excel(request):
    """Export student timetable to Excel"""
    students = AdmittedStudent.objects.all().order_by('full_name')
    
    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Student Timetable"
    
    # Headers
    headers = ['Student Name', 'Gender', 'Course', 'Theory Batch', 'Practical Batch', 'Admission Date']
    ws.append(headers)
    
    # Style header
    header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF')
    
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # Add data
    for student in students:
        theory_display = next(
            (display for slot, display in [
                ('08:00-09:00', '8:00 AM - 9:00 AM'),
                ('09:00-10:00', '9:00 AM - 10:00 AM'),
                ('10:00-11:00', '10:00 AM - 11:00 AM'),
                ('11:00-12:00', '11:00 AM - 12:00 PM'),
                ('12:00-13:00', '12:00 PM - 1:00 PM'),
                ('15:00-16:00', '3:00 PM - 4:00 PM'),
                ('16:00-17:00', '4:00 PM - 5:00 PM'),
                ('17:00-18:00', '5:00 PM - 6:00 PM'),
                ('18:00-19:00', '6:00 PM - 7:00 PM'),
            ] if slot == student.theory_batch_time),
            student.theory_batch_time or 'Not Assigned'
        )
        
        practical_display = next(
            (display for slot, display in [
                ('08:00-09:00', '8:00 AM - 9:00 AM'),
                ('09:00-10:00', '9:00 AM - 10:00 AM'),
                ('10:00-11:00', '10:00 AM - 11:00 AM'),
                ('11:00-12:00', '11:00 AM - 12:00 PM'),
                ('12:00-13:00', '12:00 PM - 1:00 PM'),
                ('15:00-16:00', '3:00 PM - 4:00 PM'),
                ('16:00-17:00', '4:00 PM - 5:00 PM'),
                ('17:00-18:00', '5:00 PM - 6:00 PM'),
                ('18:00-19:00', '6:00 PM - 7:00 PM'),
            ] if slot == student.practical_batch_time),
            student.practical_batch_time or 'Not Assigned'
        )
        
        ws.append([
            student.full_name,
            student.gender,
            student.course or 'N/A',
            theory_display,
            practical_display,
            student.admission_date.strftime('%Y-%m-%d')
        ])
    
    # Adjust column widths
    ws.column_dimensions['A'].width = 25
    ws.column_dimensions['B'].width = 12
    ws.column_dimensions['C'].width = 18
    ws.column_dimensions['D'].width = 18
    ws.column_dimensions['E'].width = 18
    ws.column_dimensions['F'].width = 15
    
    # Return as attachment
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="student_timetable.xlsx"'
    wb.save(response)
    return response


@login_required
@staff_member_required
def export_attendance_report_excel(request):
    """Export attendance reports to Excel"""
    report_type = request.GET.get('report_type', 'student')
    
    wb = openpyxl.Workbook()
    ws = wb.active
    
    if report_type == 'student':
        ws.title = "Student Attendance"
        
        # Headers
        headers = ['Student Name', 'Course', 'Total Days', 'Present Days', 'Absent Days', 'Attendance %']
        ws.append(headers)
        
        # Style header
        header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
        header_font = Font(bold=True, color='FFFFFF')
        
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
        
        # Add data
        students = AdmittedStudent.objects.all().order_by('full_name')
        for student in students:
            total_records = student.attendance_records.count()
            present_count = student.attendance_records.filter(
                Q(theory_attendance='P') | Q(practical_attendance='P')
            ).count()
            absent_count = total_records - present_count
            
            if total_records > 0:
                percentage = (present_count / total_records) * 100
            else:
                percentage = 0
            
            ws.append([
                student.full_name,
                student.course or 'N/A',
                total_records,
                present_count,
                absent_count,
                f"{percentage:.2f}%"
            ])
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 18
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 15
        ws.column_dimensions['F'].width = 15
    
    # Return as attachment
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="attendance_report_{report_type}.xlsx"'
    wb.save(response)
    return response


# ================= BATCH MANAGEMENT VIEWS =================

@login_required
@staff_member_required
@require_http_methods(["POST"])
@csrf_protect
def create_batch(request):
    """Create a new batch - AJAX endpoint"""
    try:
        data = json.loads(request.body)
        batch_type = data.get('batch_type', '').strip()
        time_slot = data.get('time_slot', '').strip()
        capacity = data.get('capacity', 50)
        
        # Validate inputs
        if not batch_type or not time_slot:
            return JsonResponse({
                'success': False,
                'error': 'Batch type and time slot are required'
            }, status=400)
        
        if batch_type not in ['Theory', 'Practical']:
            return JsonResponse({
                'success': False,
                'error': 'Invalid batch type. Must be Theory or Practical'
            }, status=400)
        
        # Validate time slot
        valid_slots = [
            '08:00-09:00', '09:00-10:00', '10:00-11:00', '11:00-12:00',
            '12:00-13:00', '15:00-16:00', '16:00-17:00', '17:00-18:00', '18:00-19:00'
        ]
        if time_slot not in valid_slots:
            return JsonResponse({
                'success': False,
                'error': 'Invalid time slot'
            }, status=400)
        
        # Convert capacity to int
        try:
            capacity = int(capacity) if capacity else 50
            if capacity < 1:
                capacity = 50
        except (ValueError, TypeError):
            capacity = 50
        
        # Check if batch already exists
        from .models import Batch
        existing_batch = Batch.objects.filter(
            batch_type=batch_type,
            time_slot=time_slot,
            course__isnull=True
        ).first()
        
        if existing_batch:
            return JsonResponse({
                'success': False,
                'error': f'{batch_type} batch at {time_slot} already exists'
            }, status=400)
        
        # Create the batch
        batch = Batch.objects.create(
            batch_type=batch_type,
            time_slot=time_slot,
            capacity=capacity,
            course=None
        )
        
        return JsonResponse({
            'success': True,
            'message': f'✅ New {batch_type} batch created at {batch.get_time_slot_display()}',
            'batch': {
                'id': batch.id,
                'type': batch_type,
                'time_slot': time_slot,
                'display': batch.get_time_slot_display(),
                'capacity': capacity
            }
        }, status=201)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        print(f"Error creating batch: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)


@login_required
@staff_member_required
@require_http_methods(["POST"])
@csrf_protect
def delete_batch(request, batch_id):
    """Delete a batch - AJAX endpoint"""
    try:
        from .models import Batch
        
        batch = get_object_or_404(Batch, id=batch_id)
        batch_type = batch.batch_type
        time_slot_display = batch.get_time_slot_display()
        
        # Unassign all students from this batch before deleting
        if batch_type == 'Theory':
            students = AdmittedStudent.objects.filter(theory_batch_time=batch.time_slot)
            student_count = students.count()
            # Unassign students
            students.update(theory_batch_time=None)
        else:
            students = AdmittedStudent.objects.filter(practical_batch_time=batch.time_slot)
            student_count = students.count()
            # Unassign students
            students.update(practical_batch_time=None)
        
        # Delete the batch
        batch.delete()
        
        message = f'✅ {batch_type} batch at {time_slot_display} has been deleted'
        if student_count > 0:
            message += f' ({student_count} student(s) were unassigned)'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'students_unassigned': student_count
        })
    
    except Batch.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Batch not found'
        }, status=404)
    except Exception as e:
        print(f"Error deleting batch: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)


@login_required
@staff_member_required
def get_batch_list(request):
    """Get updated list of theory and practical batches - AJAX endpoint"""
    try:
        from .models import Batch
        
        time_slots = [
            ('08:00-09:00', '8:00 AM - 9:00 AM'),
            ('09:00-10:00', '9:00 AM - 10:00 AM'),
            ('10:00-11:00', '10:00 AM - 11:00 AM'),
            ('11:00-12:00', '11:00 AM - 12:00 PM'),
            ('12:00-13:00', '12:00 PM - 1:00 PM'),
            ('15:00-16:00', '3:00 PM - 4:00 PM'),
            ('16:00-17:00', '4:00 PM - 5:00 PM'),
            ('17:00-18:00', '5:00 PM - 6:00 PM'),
            ('18:00-19:00', '6:00 PM - 7:00 PM'),
        ]
        
        # Get theory batches that actually exist in database
        theory_batches = []
        for batch in Batch.objects.filter(batch_type='Theory', course__isnull=True):
            count = AdmittedStudent.objects.filter(theory_batch_time=batch.time_slot).count()
            display = dict(time_slots).get(batch.time_slot, batch.time_slot)
            theory_batches.append({
                'id': batch.id,
                'slot': batch.time_slot,
                'display': display,
                'count': count,
                'capacity': batch.capacity,
                'exists': True
            })
        
        # Get practical batches that actually exist in database
        practical_batches = []
        for batch in Batch.objects.filter(batch_type='Practical', course__isnull=True):
            count = AdmittedStudent.objects.filter(practical_batch_time=batch.time_slot).count()
            display = dict(time_slots).get(batch.time_slot, batch.time_slot)
            practical_batches.append({
                'id': batch.id,
                'slot': batch.time_slot,
                'display': display,
                'count': count,
                'capacity': batch.capacity,
                'exists': True
            })
        
        # Total statistics
        total_students = AdmittedStudent.objects.count()
        students_with_theory = AdmittedStudent.objects.filter(theory_batch_time__isnull=False).exclude(theory_batch_time='').count()
        students_with_practical = AdmittedStudent.objects.filter(practical_batch_time__isnull=False).exclude(practical_batch_time='').count()
        
        return JsonResponse({
            'success': True,
            'theory_batches': theory_batches,
            'practical_batches': practical_batches,
            'total_students': total_students,
            'students_with_theory': students_with_theory,
            'students_with_practical': students_with_practical,
            'students_without_batch': total_students - max(students_with_theory, students_with_practical)
        })
    
    except Exception as e:
        print(f"Error getting batch list: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@staff_member_required
def get_batch_id(request):
    """Helper endpoint to get batch ID by type and time_slot"""
    try:
        batch_type = request.GET.get('type')
        time_slot = request.GET.get('time_slot')
        
        if not batch_type or not time_slot:
            return JsonResponse({
                'success': False,
                'error': 'Missing type or time_slot parameter'
            }, status=400)
        
        # Find the batch - match the same filter used in create_batch
        batch = Batch.objects.get(
            batch_type=batch_type, 
            time_slot=time_slot,
            course__isnull=True
        )
        
        return JsonResponse({
            'success': True,
            'batch_id': batch.id
        })
    
    except Batch.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Batch not found'
        }, status=404)
    except Exception as e:
        print(f"Error getting batch ID: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@staff_member_required
@require_http_methods(["POST"])
@csrf_protect
def edit_batch(request, batch_id):
    """Edit a batch - AJAX endpoint"""
    try:
        import json
        from .models import Batch
        
        batch = get_object_or_404(Batch, id=batch_id)
        data = json.loads(request.body)
        
        new_time_slot = data.get('time_slot')
        new_capacity = data.get('capacity')
        
        if not new_time_slot:
            return JsonResponse({
                'success': False,
                'error': 'Time slot is required'
            }, status=400)
        
        # Validate time slot
        valid_slots = [
            '08:00-09:00', '09:00-10:00', '10:00-11:00', '11:00-12:00',
            '12:00-13:00', '15:00-16:00', '16:00-17:00', '17:00-18:00', '18:00-19:00'
        ]
        if new_time_slot not in valid_slots:
            return JsonResponse({
                'success': False,
                'error': 'Invalid time slot'
            }, status=400)
        
        # Check if another batch already has this time slot
        existing_batch = Batch.objects.filter(
            batch_type=batch.batch_type,
            time_slot=new_time_slot,
            course__isnull=True
        ).exclude(id=batch.id).first()
        
        if existing_batch:
            return JsonResponse({
                'success': False,
                'error': f'A {batch.batch_type.lower()} batch already exists at {new_time_slot}'
            }, status=400)
        
        # Update batch
        batch.time_slot = new_time_slot
        if new_capacity:
            try:
                capacity = int(new_capacity)
                if capacity > 0:
                    batch.capacity = capacity
            except (ValueError, TypeError):
                pass
        
        batch.save()
        
        return JsonResponse({
            'success': True,
            'message': f'✅ {batch.batch_type} batch updated successfully',
            'batch': {
                'id': batch.id,
                'type': batch.batch_type,
                'time_slot': batch.time_slot,
                'capacity': batch.capacity
            }
        })
    
    except Batch.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Batch not found'
        }, status=404)
    except Exception as e:
        print(f"Error editing batch: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)


@login_required
@staff_member_required
def get_batch_students(request):
    """Get all students in a specific batch"""
    try:
        batch_type = request.GET.get('batch_type', '')
        time_slot = request.GET.get('time_slot', '')
        
        if not batch_type or not time_slot:
            return JsonResponse({
                'success': False,
                'error': 'Missing batch_type or time_slot'
            }, status=400)
        
        # Get all students in this batch
        if batch_type == 'Theory':
            students = AdmittedStudent.objects.filter(
                theory_batch_time=time_slot
            ).values(
                'id', 'full_name', 'gender', 
                'theory_batch_time', 'practical_batch_time'
            ).order_by('full_name')
        else:  # Practical
            students = AdmittedStudent.objects.filter(
                practical_batch_time=time_slot
            ).values(
                'id', 'full_name', 'gender',
                'theory_batch_time', 'practical_batch_time'
            ).order_by('full_name')
        
        students_list = list(students)
        
        return JsonResponse({
            'success': True,
            'students': students_list
        })
    except Exception as e:
        print(f"Error fetching batch students: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@staff_member_required
def update_batch_students(request):
    """Update student batch assignments"""
    try:
        data = json.loads(request.body)
        changes = data.get('changes', [])
        
        for change in changes:
            student_id = change.get('student_id')
            field_type = change.get('type')
            value = change.get('value')
            
            student = AdmittedStudent.objects.get(id=student_id)
            
            if field_type == 'theory_batch_time':
                student.theory_batch_time = value if value else None
            elif field_type == 'practical_batch_time':
                student.practical_batch_time = value if value else None
            
            student.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Updated {len(changes)} student(s)'
        })
    except AdmittedStudent.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Student not found'
        }, status=404)
    except Exception as e:
        print(f"Error updating batch students: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@staff_member_required
def get_all_students(request):
    """Get all admitted students for adding to batches"""
    try:
        students = AdmittedStudent.objects.all().values(
            'id', 'full_name', 'gender'
        ).order_by('full_name')
        
        return JsonResponse({
            'success': True,
            'students': list(students)
        })
    except Exception as e:
        print(f"Error fetching students: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def get_student_detail_batch(request, student_id):
    """Get student details for batch modal display"""
    try:
        student = AdmittedStudent.objects.get(id=student_id)
        
        data = {
            'success': True,
            'student': {
                'id': student.id,
                'full_name': student.full_name,
                'gender': student.gender,
                'mobile_own': student.mobile_own,
                'email': student.email or '',
                'course': student.course or '',
                'theory_batch_time': student.theory_batch_time or '',
                'practical_batch_time': student.practical_batch_time or '',
                'admission_date': student.admission_date.strftime('%Y-%m-%d') if student.admission_date else '',
                'address': student.address or '',
                'city': student.city or '',
                'district': student.district or '',
                'pincode': student.pin_code or '',
                'total_fees': float(student.total_fees) if student.total_fees else 0,
                'paid_fees': float(student.paid_fees) if student.paid_fees else 0,
                'remaining_fees': float(student.remaining_fees) if student.remaining_fees else 0,
            }
        }
        
        return JsonResponse(data)
    except AdmittedStudent.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Student not found'
        }, status=404)
    except Exception as e:
        print(f"Error fetching student details: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ================= UPDATE BATCH CAPACITY =================
@login_required
def update_batch_capacity(request):
    """Update batch capacity"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)
    
    try:
        data = json.loads(request.body)
        batch_id = data.get('batch_id')
        new_capacity = data.get('capacity')
        
        if not batch_id or not new_capacity:
            return JsonResponse({'success': False, 'error': 'Batch ID and capacity are required'}, status=400)
        
        # Get the batch
        batch = Batch.objects.get(id=batch_id)
        
        # Update capacity
        batch.capacity = int(new_capacity)
        batch.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Batch capacity updated to {new_capacity}',
            'batch': {
                'id': batch.id,
                'capacity': batch.capacity
            }
        })
    
    except Batch.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Batch not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except ValueError as e:
        return JsonResponse({'success': False, 'error': f'Invalid capacity value: {str(e)}'}, status=400)
    except Exception as e:
        print(f"Error updating batch capacity: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
