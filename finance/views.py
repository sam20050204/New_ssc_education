from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.html import escape
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from core.forms import FeePaymentForm
from core.models import AdmittedStudent
from core.services.fee_service import record_fee_payment


@login_required
def fees_payment(request):
    return render(request, "core/fees_payment.html", {"active_page": "fees_payment"})


@login_required
def search_students_for_payment(request):
    query = request.GET.get("q", "").strip()
    if len(query) < 2:
        return JsonResponse({"students": []})

    students = (
        AdmittedStudent.objects.filter(is_archived=False)
        .filter(Q(full_name__icontains=query) | Q(student_name__icontains=query) | Q(mobile_own__icontains=query) | Q(student_id__icontains=query))
        .order_by("full_name")[:10]
    )

    return JsonResponse(
        {
            "students": [
                {
                    "id": student.id,
                    "student_id": student.student_id,
                    "full_name": escape(student.full_name or ""),
                    "mobile_own": escape(student.mobile_own or ""),
                    "course": escape(student.custom_course if student.course == "Other" and student.custom_course else student.course or ""),
                }
                for student in students
            ]
        }
    )


@login_required
@csrf_protect
@require_http_methods(["POST"])
def submit_fee_payment(request):
    form = FeePaymentForm(
        {
            "student": request.POST.get("student_id"),
            "amount": request.POST.get("amount"),
            "payment_mode": request.POST.get("payment_mode"),
            "payment_date": request.POST.get("payment_date"),
            "remarks": request.POST.get("remarks", ""),
        }
    )

    if not form.is_valid():
        errors = [str(error) for field_errors in form.errors.values() for error in field_errors]
        return JsonResponse({"success": False, "error": " | ".join(errors) if errors else "Invalid payment data."}, status=400)

    try:
        payment_date = datetime.strptime(form.cleaned_data["payment_date"].strftime("%Y-%m-%d"), "%Y-%m-%d").date()
        payment = record_fee_payment(
            student_id=form.cleaned_data["student"].pk,
            amount=form.cleaned_data["amount"],
            payment_mode=form.cleaned_data["payment_mode"],
            payment_date=payment_date,
            remarks=form.cleaned_data.get("remarks", ""),
            actor=request.user,
            request=request,
        )
    except AdmittedStudent.DoesNotExist:
        return JsonResponse({"success": False, "error": "Student not found."}, status=404)
    except ValueError as exc:
        return JsonResponse({"success": False, "error": str(exc)}, status=400)

    return JsonResponse(
        {
            "success": True,
            "message": f"Payment recorded with receipt {payment.receipt_no}.",
            "receipt_no": payment.receipt_no,
            "student": payment.student.full_name,
            "student_id": payment.student.student_id,
            "amount": str(payment.amount),
            "remaining_fees": str(payment.remaining_after_this),
        }
    )
