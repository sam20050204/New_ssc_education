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
from datetime import datetime, timedelta
from decimal import Decimal
import json
import shutil
import os
from django.db.models import Sum, Count, Q
from .models import Student, FeePayment, StudentFinanceDetail, Enquiry, AdmittedStudent, Course

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
        custom_course = request.POST.get("other_course", "")
        address = request.POST.get("address", "")
        city = request.POST.get("city", "")
        taluka = request.POST.get("taluka", "")
        district = request.POST.get("district", "")

        Enquiry.objects.create(
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

        messages.success(request, "Enquiry submitted successfully!")
        return redirect("home")

    all_courses = Course.objects.all().order_by('name')
    
    return render(request, "core/home.html", {
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
    
    monthly_data = {str(i): 0 for i in range(1, 13)}
    
    if selected_year:
        year_students = AdmittedStudent.objects.filter(admission_date__year=selected_year)
    else:
        current_year = datetime.now().year
        year_students = AdmittedStudent.objects.filter(admission_date__year=current_year)
    
    for student in year_students:
        month = str(student.admission_date.month)
        monthly_data[month] = monthly_data.get(month, 0) + 1
    
    course_distribution_json = json.dumps(course_distribution)
    monthly_data_json = json.dumps(monthly_data)
    
    context = {
        "enquiry_count": enquiry_count,
        "mscit_count": mscit_count,
        "klic_count": klic_count,
        "available_years": available_years,
        "selected_year": selected_year,
        "active_page": "dashboard",
        "course_distribution": course_distribution_json,
        "monthly_data": monthly_data_json,
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
        try:
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
            
            # NEW: Get batch information
            batch_month = request.POST.get("batch_month", "")
            batch_year = request.POST.get("batch_year", "")
            
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
                total_fees=total_fees,
                photo=photo,
                batch_month=batch_month,  # NEW
                batch_year=batch_year,    # NEW
            )
            
            messages.success(request, f"Admission for {full_name} has been successfully recorded! Total Fees: ₹{total_fees}")
            return redirect("new_admission")
            
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
    
    # Get enquiry data from session if available
    enquiry_data = request.session.get('enquiry_conversion', {})
    
    # Get all courses from database
    all_courses = Course.objects.all().order_by('name')
    
    return render(request, "core/new_admission.html", {
        "active_page": "new_admission",
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
        
        if not course_name:
            return JsonResponse({
                'success': False,
                'message': 'Course name cannot be empty'
            }, status=400)
        
        if Course.objects.filter(name__iexact=course_name).exists():
            return JsonResponse({
                'success': False,
                'message': 'This course already exists in database!'
            }, status=400)
        
        course = Course.objects.create(
            name=course_name,
            duration='To be defined'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Course "{course_name}" added successfully!',
            'course_id': course.id,
            'course_name': course.name
        }, status=201)
    
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
            # Extract time from datetime
            payment_time = payment.payment_date.strftime('%H:%M') if payment.payment_date else 'N/A'
            
            payment_history.append({
                'id': payment.id,
                'payment_date': payment.payment_date.strftime('%d-%m-%Y') if payment.payment_date else '',
                'payment_time': payment_time,
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
        paid_fees = request.POST.get('paid_fees')
        
        if total_fees:
            student.total_fees = Decimal(total_fees)
        
        if paid_fees:
            student.paid_fees = Decimal(paid_fees)
        
        if request.FILES.get('photo'):
            student.photo = request.FILES['photo']
        
        student.save()
        
        # Update StudentFinanceDetail if total_fees changed
        if total_fees or paid_fees:
            finance_detail, created = StudentFinanceDetail.objects.get_or_create(student=student)
            # The profit will be calculated dynamically based on student.paid_fees and total_mkcl_fees
            finance_detail.save()
        
        messages.success(request, 'Student details updated successfully!')
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

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
            remarks = request.POST.get('remarks', '')
            
            # Debug logging
            print(f"Received payment data: student_id={student_id}, amount={amount}, payment_mode={payment_mode}")
            
            # Validate inputs
            if not student_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Student ID is required'
                }, status=400)
            
            if not amount:
                return JsonResponse({
                    'success': False,
                    'error': 'Payment amount is required'
                }, status=400)
            
            if not payment_mode:
                return JsonResponse({
                    'success': False,
                    'error': 'Payment mode is required'
                }, status=400)
            
            # Convert amount to Decimal
            try:
                amount = Decimal(str(amount))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid amount format'
                }, status=400)
            
            # Validate amount
            if amount <= 0:
                return JsonResponse({
                    'success': False,
                    'error': 'Payment amount must be greater than zero'
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
                
                # Create payment record
                payment = FeePayment.objects.create(
                    student=student,
                    amount=amount,
                    payment_mode=payment_mode,
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
                    'date': payment.payment_date.strftime('%d-%m-%Y'),
                    'time': payment.payment_date.strftime('%I:%M %p'),
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
                'payment_date': receipt.payment_date.strftime('%Y-%m-%d'),
                'payment_time': receipt.payment_date.strftime('%I:%M %p'),
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
            payment.payment_date = data['payment_date']
        
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
            ws.cell(row=row_num, column=5).value = payment.payment_date.strftime('%d-%m-%Y %I:%M %p')
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
                except:
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
            except:
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
    
    # Calculate total profit from StudentFinanceDetail table using same logic as student_finance_details view
    total_profit = Decimal('0.00')
    for student in students:
        # Get or create finance detail record
        finance_detail, created = StudentFinanceDetail.objects.get_or_create(
            student=student,
            defaults={
                'first_installment': Decimal('0.00'),
                'second_installment': Decimal('0.00'),
                'third_installment': Decimal('0.00'),
                'fees_paid_to_mkcl_1': Decimal('0.00'),
                'fees_paid_to_mkcl_2': Decimal('0.00'),
            }
        )
        
        # Get course name for defaults logic
        course_name = student.custom_course if student.course == 'Other' and student.custom_course else student.course
        
        # Calculate fees paid to MKCL with course-based defaults
        mkcl_1 = finance_detail.fees_paid_to_mkcl_1 or Decimal('0.00')
        mkcl_2 = finance_detail.fees_paid_to_mkcl_2 or Decimal('0.00')
        
        # Apply course-based defaults only if values are 0
        if mkcl_1 == Decimal('0.00') or mkcl_1 is None:
            if course_name == 'MS-CIT':
                mkcl_1 = Decimal('1230.00')
            else:
                mkcl_1 = Decimal('500.00')
        
        if mkcl_2 == Decimal('0.00') or mkcl_2 is None:
            if course_name == 'MS-CIT':
                mkcl_2 = Decimal('570.00')
            else:
                mkcl_2 = Decimal('500.00')
        
        mkcl_total = mkcl_1 + mkcl_2
        
        # Get fee payments for this student - ordered by payment_date (oldest first)
        fee_payments = FeePayment.objects.filter(student=student).order_by('payment_date')
        
        # Extract installment amounts from FeePayment records
        first_inst = Decimal('0.00')
        second_inst = Decimal('0.00')
        third_inst = Decimal('0.00')
        
        if len(fee_payments) >= 1:
            first_inst = fee_payments[0].amount
        if len(fee_payments) >= 2:
            second_inst = fee_payments[1].amount
        if len(fee_payments) >= 3:
            third_inst = fee_payments[2].amount
        
        # Calculate profit as (Total Fees Paid By Learner) - (Total Fees Paid to MKCL)
        learner_total_paid = first_inst + second_inst + third_inst
        profit = learner_total_paid - mkcl_total
        total_profit += profit
    
    context = {
        'available_years': available_years,
        'selected_year': selected_year,
        'total_profit': total_profit,
        'total_admitted': students.count(),
        'student_count': students.count(),
    }
    return render(request, 'core/statistics.html', context)

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
        
        # Calculate fees paid to MKCL with course-based defaults
        mkcl_1 = finance_detail.fees_paid_to_mkcl_1 or Decimal('0.00')
        mkcl_2 = finance_detail.fees_paid_to_mkcl_2 or Decimal('0.00')
        
        # Apply course-based defaults only if values are 0
        if mkcl_1 == Decimal('0.00') or mkcl_1 is None:
            if course_name == 'MS-CIT':
                mkcl_1 = Decimal('1230.00')
            else:
                mkcl_1 = Decimal('500.00')
        
        if mkcl_2 == Decimal('0.00') or mkcl_2 is None:
            if course_name == 'MS-CIT':
                mkcl_2 = Decimal('570.00')
            else:
                mkcl_2 = Decimal('500.00')
        
        mkcl_total = mkcl_1 + mkcl_2
        
        # Get fee payments for this student - ordered by payment_date (oldest first)
        fee_payments = FeePayment.objects.filter(student=student).order_by('payment_date')
        
        # Extract installment amounts from FeePayment records
        first_inst = Decimal('0.00')
        second_inst = Decimal('0.00')
        third_inst = Decimal('0.00')
        
        if len(fee_payments) >= 1:
            first_inst = fee_payments[0].amount
        if len(fee_payments) >= 2:
            second_inst = fee_payments[1].amount
        if len(fee_payments) >= 3:
            third_inst = fee_payments[2].amount
        
        # Calculate profit as (Total Fees Paid By Learner) - (Total Fees Paid to MKCL)
        learner_total_paid = first_inst + second_inst + third_inst
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
            'learner_name': student.full_name,
            'student_id': student.id,  # Using student ID as identifier
            'mobile_no': student.mobile_own,
            'batch': student.batch_display,
            'course': course_name,
            'first_inst': first_inst,
            'second_inst': second_inst,
            'third_inst': third_inst,
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
            
            # Update the appropriate field
            if field == 'first_inst':
                finance_detail.first_installment = value
            elif field == 'second_inst':
                finance_detail.second_installment = value
            elif field == 'third_inst':
                finance_detail.third_installment = value
            elif field == 'mkcl_1':
                finance_detail.fees_paid_to_mkcl_1 = value
            elif field == 'mkcl_2':
                finance_detail.fees_paid_to_mkcl_2 = value
            
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
    selected_year = request.GET.get('year', '')
    
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
    
    # Calculate monthly profit data by course
    # Logic: For each student, calculate their total profit = (all installments paid) - (MKCL fees)
    # Then allocate that profit proportionally to the months when installments were paid
    monthly_profit_data = []
    profit_monthly_totals = {month: Decimal('0.00') for month in months}
    profit_grand_total = Decimal('0.00')
    
    for course in all_courses:
        course_profit = {'course': course}
        course_profit_total = Decimal('0.00')
        
        for month_num, month_key in enumerate(months, 1):
            # Get all students for this course
            course_students = students.filter(
                Q(course=course) | Q(custom_course=course)
            )
            
            # Calculate profit for this month from FeePayment records
            month_profit = Decimal('0.00')
            
            for student in course_students:
                # Get ALL fee payments for this student
                all_fee_payments = FeePayment.objects.filter(student=student).order_by('payment_date')
                
                if not all_fee_payments.exists():
                    continue
                
                # Calculate total profit for this student (same as student_finance_details view)
                # Get or create finance detail to get MKCL fees
                finance_detail, _ = StudentFinanceDetail.objects.get_or_create(
                    student=student,
                    defaults={
                        'fees_paid_to_mkcl_1': Decimal('0.00'),
                        'fees_paid_to_mkcl_2': Decimal('0.00'),
                    }
                )
                
                # Get course name for MKCL defaults
                course_name = student.custom_course if student.course == 'Other' and student.custom_course else student.course
                
                # Get MKCL fees with defaults (same logic as student_finance_details)
                mkcl_1 = finance_detail.fees_paid_to_mkcl_1 or Decimal('0.00')
                mkcl_2 = finance_detail.fees_paid_to_mkcl_2 or Decimal('0.00')
                
                if mkcl_1 == Decimal('0.00'):
                    mkcl_1 = Decimal('1230.00') if course_name == 'MS-CIT' else Decimal('500.00')
                
                if mkcl_2 == Decimal('0.00'):
                    mkcl_2 = Decimal('570.00') if course_name == 'MS-CIT' else Decimal('500.00')
                
                mkcl_total = mkcl_1 + mkcl_2
                
                # Calculate total fees paid (sum of all installments)
                total_fees_paid = all_fee_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
                
                # Calculate total profit = total fees paid - MKCL fees
                total_profit_student = total_fees_paid - mkcl_total
                
                # Now allocate this profit proportionally based on which payments were made in this month
                # Get payments made in this specific month
                payments_in_month = all_fee_payments.filter(payment_date__month=month_num)
                
                if selected_year:
                    payments_in_month = payments_in_month.filter(payment_date__year=int(selected_year))
                
                if payments_in_month.exists():
                    # Calculate what portion of total fees were paid in this month
                    fees_paid_this_month = payments_in_month.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
                    
                    # Allocate profit proportionally
                    if total_fees_paid > 0:
                        profit_this_month = (fees_paid_this_month / total_fees_paid) * total_profit_student
                        month_profit += profit_this_month
            
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
