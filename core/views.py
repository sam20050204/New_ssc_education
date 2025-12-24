from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models.functions import ExtractYear
from django.db import transaction
import csv
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from io import BytesIO
from datetime import datetime
from decimal import Decimal

from .models import Enquiry, AdmittedStudent, Course, Student, FeePayment


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
    selected_year = request.GET.get('year', '')
    
    available_years = (
        Enquiry.objects
        .annotate(year=ExtractYear('created_at'))
        .values_list('year', flat=True)
        .distinct()
        .order_by('-year')
    )
    
    enquiries = Enquiry.objects.all()
    
    if selected_year:
        enquiries = enquiries.filter(created_at__year=selected_year)
    
    enquiry_count = enquiries.count()
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
    search = request.GET.get("search", "")
    month = request.GET.get("month", "")
    year = request.GET.get("year", "")
    course = request.GET.get("course", "")
    
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
        'total_fees': float(student.total_fees),
        'paid_fees': float(student.paid_fees),
        'remaining_fees': float(student.remaining_fees),
    }
    
    return JsonResponse(data)


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
        
        if request.FILES.get('photo'):
            student.photo = request.FILES['photo']
        
        student.save()
        
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


# ================= SUBMIT FEE PAYMENT =================
@login_required
def submit_fee_payment(request):
    if request.method == 'POST':
        try:
            student_id = request.POST.get('student_id')
            amount = Decimal(request.POST.get('amount'))
            payment_mode = request.POST.get('payment_mode')
            remarks = request.POST.get('remarks', '')
            
            with transaction.atomic():
                student = AdmittedStudent.objects.select_for_update().get(id=student_id)
                
                # Validate amount
                if amount <= 0:
                    return JsonResponse({
                        'success': False,
                        'error': 'Payment amount must be greater than zero'
                    })
                
                if amount > student.remaining_fees:
                    return JsonResponse({
                        'success': False,
                        'error': f'Payment amount cannot exceed remaining fees (₹{student.remaining_fees})'
                    })
                
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
                
                receipt_data = {
                    'receipt_no': payment.receipt_no,
                    'date': payment.payment_date.strftime('%d-%m-%Y'),
                    'time': payment.payment_date.strftime('%I:%M %p'),
                    'student_name': student.full_name,
                    'course': course_name,
                    'mobile': student.mobile_own,
                    'payment_mode': payment_mode,
                    'total_fees': f"{float(student.total_fees):.2f}",
                    'previous_paid': f"{float(payment.paid_before_this):.2f}",
                    'amount_paid': f"{float(amount):.2f}",
                    'remaining_fees': f"{float(payment.remaining_after_this):.2f}",
                    'amount_in_words': number_to_words(float(amount))
                }
                
                return JsonResponse({
                    'success': True,
                    'receipt': receipt_data
                })
                
        except AdmittedStudent.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Student not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


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
    
    # Split into integer and decimal parts
    rupees = int(num)
    paise = int(round((num - rupees) * 100))
    
    result = ''
    
    # Convert crores
    if rupees >= 10000000:
        result += convert_less_than_thousand(rupees // 10000000) + 'Crore '
        rupees %= 10000000
    
    # Convert lakhs
    if rupees >= 100000:
        result += convert_less_than_thousand(rupees // 100000) + 'Lakh '
        rupees %= 100000
    
    # Convert thousands
    if rupees >= 1000:
        result += convert_less_than_thousand(rupees // 1000) + 'Thousand '
        rupees %= 1000
    
    # Convert remaining
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
    students = Student.objects.filter(is_active=True)
    
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
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Admitted Students"
    
    headers = [
        'S.No', 'Name', 'Phone', 'Email', 'Course', 'Admission Date',
        'Address', 'City', 'State', 'Pincode', 'Parent Name', 'Parent Phone',
        'Qualification', 'Date of Birth', 'Total Fees', 'Paid Fees', 'Remaining Fees'
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
    
    filename = f'admitted_students_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

    