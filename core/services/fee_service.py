from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import F

from core.audit_logs import log_audit_event
from core.models import AdmittedStudent, FeePayment, StudentFinanceDetail


def _quantize_amount(raw_amount):
    try:
        amount = Decimal(str(raw_amount).strip()).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("Invalid amount.") from exc

    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    if amount > Decimal("10000000.00"):
        raise ValueError("Amount exceeds the maximum allowed limit.")
    return amount


def sync_finance_installments(student):
    payments = list(student.fee_payments.order_by("payment_date", "created_at")[:5])
    finance_detail, _ = StudentFinanceDetail.objects.get_or_create(student=student)

    installment_fields = [
        "first_installment",
        "second_installment",
        "third_installment",
        "fourth_installment",
        "fifth_installment",
    ]

    updates = {}
    for index, field_name in enumerate(installment_fields):
        updates[field_name] = payments[index].amount if index < len(payments) else Decimal("0.00")

    for field_name, value in updates.items():
        setattr(finance_detail, field_name, value)

    finance_detail.save(update_fields=[*installment_fields, "updated_at"])
    return finance_detail


@transaction.atomic
def record_fee_payment(*, student_id, amount, payment_mode, payment_date, remarks="", actor=None, request=None):
    amount = _quantize_amount(amount)
    student = AdmittedStudent.objects.select_for_update().get(pk=student_id, is_archived=False)

    if amount > student.remaining_fees:
        raise ValueError(f"Payment amount cannot exceed remaining fees of Rs. {student.remaining_fees}.")

    payment = FeePayment.objects.create(
        student=student,
        amount=amount,
        payment_mode=payment_mode,
        payment_date=payment_date,
        remarks=(remarks or "").strip()[:1000],
        total_fees_at_payment=student.total_fees,
        paid_before_this=student.paid_fees,
        remaining_after_this=student.total_fees - (student.paid_fees + amount),
    )

    student.paid_fees = F("paid_fees") + amount
    student.save(update_fields=["paid_fees", "updated_at"])
    student.refresh_from_db(fields=["paid_fees", "updated_at"])

    sync_finance_installments(student)
    log_audit_event(
        action="fees.payment_recorded",
        actor=actor,
        target=payment,
        request=request,
        metadata={
            "student_id": student.student_id,
            "amount": str(amount),
            "payment_mode": payment_mode,
        },
    )
    return payment
