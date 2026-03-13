from datetime import timedelta
from django.db import transaction  
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models.functions import ExtractYear
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
import csv
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from io import BytesIO
from datetime import datetime
from decimal import Decimal
import json
import shutil
import os
from django.db.models import Sum, Count, Q
from .models import Student, FeePayment, StudentFinanceDetail, Enquiry, AdmittedStudent, Course, SalesItem, Attendance
from .forms import EnquiryForm, AdmittedStudentForm, FeePaymentForm, CourseForm
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
    
    available_years = (
        AdmittedStudent.objects
        .annotate(year=ExtractYear('admission_date'))
        .values_list('year', flat=True)
        .distinct()
        .order_by('-year')
    )
    
    students = AdmittedStudent.objects.all()
    
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
    
    # Prepare data for clustered bar chart: admissions by course for each month
    if selected_year:
        year_students = AdmittedStudent.objects.filter(admission_date__year=selected_year)
    else:
        current_year = datetime.now().year
        year_students = AdmittedStudent.objects.filter(admission_date__year=current_year)
    
    # Get unique courses
    unique_courses = set()
    for student in year_students:
        course_name = student.custom_course if student.course == 'Other' and student.custom_course else student.course
        unique_courses.add(course_name)
    unique_courses = sorted(list(unique_courses))
    
    # Create monthly data by course
    monthly_by_course = {}
    for course in unique_courses:
        monthly_by_course[course] = {str(i): 0 for i in range(1, 13)}
    
    # Populate with actual data
    for student in year_students:
        if student.admission_date:
            course_name = student.custom_course if student.course == 'Other' and student.custom_course else student.course
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


@login_required
@require_http_methods(["POST"])
def save_attendance_ajax(request):
    """AJAX endpoint to save attendance for a single date and return JSON response."""
    try:
        data = json.loads(request.body)
        date_str = data.get('date')
        present_ids = data.get('present_ids', [])

        # Parse and validate date
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Remove attendance records for students not present
        Attendance.objects.filter(date=selected_date).exclude(student_id__in=present_ids).delete()

        # Create or update present records
        for sid in present_ids:
            try:
                sid = int(sid)
                Attendance.objects.update_or_create(
                    student_id=sid,
                    date=selected_date,
                    defaults={'status': 'P'}
                )
            except (ValueError, AdmittedStudent.DoesNotExist):
                pass

        return JsonResponse({
            'success': True,
            'message': f'Attendance updated for {selected_date}',
            'present_count': len(present_ids),
            'date': str(selected_date)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def get_attendance_data(request):
    """AJAX endpoint to fetch filtered attendance data with pagination."""
    from datetime import date as _date
    
    date_str = request.GET.get('date')
    course_filter = request.GET.get('course', '')
    batch_filter = request.GET.get('batch', '')
    page_num = request.GET.get('page', 1)
    
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except Exception:
            selected_date = _date.today()
    else:
        selected_date = _date.today()

    # Get all students
    students = AdmittedStudent.objects.filter().order_by('full_name')

    # Apply filters
    if course_filter:
        students = students.filter(course=course_filter)
    if batch_filter:
        students = students.filter(batch_month=batch_filter)

    # Get attendance for the selected date
    attendance_qs = Attendance.objects.filter(date=selected_date)
    attendance_map = {a.student_id: a.status for a in attendance_qs}
    present_ids = [sid for sid, st in attendance_map.items() if st == 'P']

    # Paginate
    paginator = Paginator(students, 20)
    page_obj = paginator.get_page(page_num)

    # Get available courses and batches for filter dropdowns
    all_courses = AdmittedStudent.objects.values_list('course', flat=True).distinct().order_by('course')
    all_batches = AdmittedStudent.objects.values_list('batch_month', flat=True).distinct().order_by('batch_month')

    # Build student list for response
    student_list = []
    for student in page_obj.object_list:
        student_list.append({
            'id': student.id,
            'name': student.full_name,
            'course': student.course,
            'batch': student.batch_display,
            'mobile': student.mobile_own,
            'is_present': student.id in present_ids
        })

    return JsonResponse({
        'success': True,
        'students': student_list,
        'current_page': page_obj.number,
        'total_pages': page_obj.paginator.num_pages,
        'total_count': page_obj.paginator.count,
        'selected_date': str(selected_date),
        'present_count': len(present_ids),
        'courses': list(all_courses),
        'batches': list(all_batches),
    })


@login_required
def get_attendance_chart_data(request):
    """AJAX endpoint to get last 7 days attendance summary for chart."""
    from datetime import timedelta, date as _date
    
    today = _date.today()
    start_date = today - timedelta(days=6)  # Last 7 days including today
    
    # Get attendance records for last 7 days
    attendance_records = Attendance.objects.filter(
        date__gte=start_date,
        date__lte=today,
        status='P'
    ).values('date').annotate(present_count=Count('id')).order_by('date')
    
    # Build date range with counts
    chart_data = {}
    for i in range(7):
        date = start_date + timedelta(days=i)
        chart_data[str(date)] = 0
    
    # Populate with actual data
    for record in attendance_records:
        chart_data[str(record['date'])] = record['present_count']
    
    # Get total students count
    total_students = AdmittedStudent.objects.count()
    
    return JsonResponse({
        'success': True,
        'labels': list(chart_data.keys()),
        'data': list(chart_data.values()),
        'total_students': total_students,
        'date_range': f"{start_date} to {today}"
    })


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
    
    students = AdmittedStudent.objects.all().order_by('-admission_date')
    
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
    
    available_years = (
        AdmittedStudent.objects
        .annotate(year=ExtractYear('admission_date'))
        .values_list('year', flat=True)
        .distinct()
        .order_by('-year')
    )
    
    # NEW: Get available batch months and years
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
    
    # Get all courses from database
    all_courses = Course.objects.all().order_by('name')
    
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
        
        student.student_name = request.POST.get('student_name')
        student.father_name = request.POST.get('father_name')
        student.surname = request.POST.get('surname')
        student.mother_name = request.POST.get('mother_name')
        student.full_name = request.POST.get('full_name')
        student.date_of_birth = request.POST.get('date_of_birth')
        student.admission_date = request.POST.get('admission_date')
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
        
        # NEW: Update batch information
        student.batch_month = request.POST.get('batch_month', '')
        student.batch_year = request.POST.get('batch_year', '')
        
        # Update fees information
        total_fees = request.POST.get('total_fees')
        
        if total_fees:
            student.total_fees = Decimal(total_fees)
        
        # Note: paid_fees is now readonly and should not be edited here
        # It's calculated from FeePayment records only
        
        if request.FILES.get('photo'):
            student.photo = request.FILES['photo']
        
        student.save()
        
        # Update StudentFinanceDetail if total_fees changed
        if total_fees:
            finance_detail, created = StudentFinanceDetail.objects.get_or_create(student=student)
            # The profit will be calculated dynamically based on student.paid_fees and total_mkcl_fees
            finance_detail.save()
        
        messages.success(request, 'Student details updated successfully!')
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
            'full_name': student.full_name or f"{student.student_name} {student.father_name} {student.surname}",
            'mobile_own': student.mobile_own,
            'course': course_name,
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
            'full_name': student.full_name,
            'mobile_own': student.mobile_own,
            'course': course_name
        })
    
    return JsonResponse({'students': students_data})


# ================= SUBMIT FEE PAYMENT - FIXED VERSION WITH BATCH =================
@login_required
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
                amount = Decimal(str(amount))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid amount format'
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
                
                # Update student's paid fees
                student.paid_fees += amount
                student.save()
                
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
            new_amount = Decimal(str(data.get('amount') or data.get('paid_fees', old_amount)))
            
            # Validate amount
            if new_amount <= 0:
                return JsonResponse({
                    'success': False,
                    'error': 'Amount must be greater than zero'
                }, status=400)
            
            # Update student's paid fees
            student = payment.student
            amount_difference = new_amount - old_amount
            
            with transaction.atomic():
                student.paid_fees = max(0, student.paid_fees + amount_difference)
                student.save()
                
                payment.amount = new_amount
                payment.remaining_after_this = student.total_fees - student.paid_fees
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
        'Course', 'Custom Course', 'Educational Qualification',
        'Address', 'City', 'Tehsil/Block', 'District', 'Pin Code',
        'Total Fees (₹)', 'Paid Fees (₹)', 'Remaining Fees (₹)', 'Fees % Paid',
        'Admission Date'
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
        ws.cell(row=row_num, column=13).value = student.custom_course or ''
        ws.cell(row=row_num, column=14).value = student.educational_qualification
        ws.cell(row=row_num, column=15).value = student.address
        ws.cell(row=row_num, column=16).value = student.city
        ws.cell(row=row_num, column=17).value = student.tehsil_block
        ws.cell(row=row_num, column=18).value = student.district
        ws.cell(row=row_num, column=19).value = student.pin_code
        ws.cell(row=row_num, column=20).value = float(student.total_fees)
        ws.cell(row=row_num, column=21).value = float(student.paid_fees)
        ws.cell(row=row_num, column=22).value = float(student.remaining_fees)
        percentage = (student.paid_fees / student.total_fees * 100) if student.total_fees else 0
        ws.cell(row=row_num, column=23).value = f"{percentage:.2f}%"
        ws.cell(row=row_num, column=24).value = student.admission_date.strftime('%d-%m-%Y %I:%M %p')
    
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
        
        with transaction.atomic():
            for student in students_to_delete:
                if student.photo:
                    try:
                        if student.photo.path:
                            if os.path.isfile(student.photo.path):
                                os.remove(student.photo.path)
                    except Exception as e:
                        print(f"Error deleting photo: {str(e)}")
            
            students_to_delete.delete()
        
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
    """Export database as SQLite file"""
    try:
        db_path = settings.DATABASES['default']['NAME']
        
        # Convert Path object to string
        db_path = str(db_path)
        
        # Check if file exists
        if not os.path.exists(db_path):
            return JsonResponse({'success': False, 'error': 'Database file not found'}, status=500)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'database_backup_{timestamp}.db'
        
        with open(db_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/x-sqlite3')
            response['Content-Disposition'] = f'attachment; filename="{backup_name}"'
        
        return response
    
    except Exception as e:
        print(f"Export database error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def import_database(request):
    """Import database from uploaded file"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)
    
    if 'database_file' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'No file provided'}, status=400)
    
    uploaded_file = request.FILES['database_file']
    
    # Validate file
    valid_extensions = ['db', 'sqlite', 'sqlite3']
    file_extension = uploaded_file.name.split('.')[-1].lower()
    
    if file_extension not in valid_extensions:
        return JsonResponse({'success': False, 'error': 'Invalid file type. Only .db, .sqlite, or .sqlite3 files are allowed.'}, status=400)
    
    max_size = 100 * 1024 * 1024  # 100 MB
    if uploaded_file.size > max_size:
        return JsonResponse({'success': False, 'error': 'File too large. Maximum size is 100 MB.'}, status=400)
    
    try:
        db_path = settings.DATABASES['default']['NAME']
        
        # Create backup of current database before importing
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'database_backup_before_import_{timestamp}.db'
        backup_path = os.path.join(settings.BASE_DIR, backup_name)
        shutil.copy2(db_path, backup_path)
        
        # Read the uploaded file and write to database location
        db_data = uploaded_file.read()
        
        # Close all database connections
        from django.db import connections
        connections.close_all()
        
        # Write the new database
        with open(db_path, 'wb') as f:
            f.write(db_data)
        
        return JsonResponse({
            'success': True,
            'message': f'Database imported successfully! Backup saved as {backup_name}'
        })
    
    except Exception as e:
        print(f"Import error: {str(e)}")
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
def student_daily_attendance(request):
    """View to display and record daily attendance for admitted students."""
    from datetime import date as _date
    # Parse selected date from GET or POST
    date_str = request.GET.get('date') or request.POST.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except Exception:
            selected_date = _date.today()
    else:
        selected_date = _date.today()

    if request.method == 'POST':
        # Expect checkbox inputs named 'present' with student ids
        present_ids = request.POST.getlist('present')
        # Normalize to ints
        present_ids = [int(x) for x in present_ids if x.isdigit()]

        # Remove attendance records for students not present
        Attendance.objects.filter(date=selected_date).exclude(student_id__in=present_ids).delete()

        # Create or update present records
        for sid in present_ids:
            Attendance.objects.update_or_create(
                student_id=sid,
                date=selected_date,
                defaults={'status': 'P'}
            )

        # Ensure absent records exist for other students (optional)
        # Redirect back to GET to show updated data
        messages.success(request, f"Attendance updated for {selected_date}")
        # Render updated template below

    # GET or re-render after POST
    students = AdmittedStudent.objects.filter().order_by('full_name')
    attendance_qs = Attendance.objects.filter(date=selected_date)
    attendance_map = {a.student_id: a.status for a in attendance_qs}
    present_ids = [sid for sid, st in attendance_map.items() if st == 'P']

    context = {
        'students': students,
        'attendance_map': attendance_map,
        'present_ids': present_ids,
        'selected_date': selected_date,
        'active_page': 'statistics',
    }

    return render(request, 'core/student_attendance.html', context)

@login_required
def student_finance_details(request):
    """Student Finance Details section"""
    selected_year = request.GET.get('year', '')
    
    # Get available years from AdmittedStudent
    available_years = (
        AdmittedStudent.objects
        .annotate(year=ExtractYear('admission_date'))
        .values_list('year', flat=True)
        .distinct()
        .order_by('-year')
    )
    
    # Get all admitted students for the selected year
    students = AdmittedStudent.objects.all()
    if selected_year:
        students = students.filter(admission_date__year=selected_year)
    
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
    
    context = {
        'finance_data': finance_data,
        'total_profit': total_profit,
        'selected_year': selected_year,
        'available_years': available_years,
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

