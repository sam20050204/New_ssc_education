from datetime import date
from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Q, Sum
from django.utils import timezone

from core.audit_logs import log_audit_event
from core.models import AdmittedStudent, Batch, BatchActionLog, FeePayment
from core.utils import get_time_slot_display

ACTIVE_BATCH_STATUSES = ("active",)
ENDED_BATCH_STATUSES = ("completed", "archived", "cancelled")
ADMIN_MUTATION_STATUSES = {
    "end": {"from": {"active"}, "to": "completed", "log": "ended"},
    "restore": {"from": {"completed", "archived", "cancelled"}, "to": "active", "log": "restored"},
}


def get_batch_dashboard_data():
    theory_batches = []
    for batch in Batch.objects.filter(batch_type="Theory", course__isnull=True, is_archived=False).order_by(
        "time_slot"
    ):
        theory_batches.append(_serialize_batch(batch))

    practical_batches = []
    for batch in Batch.objects.filter(batch_type="Practical", course__isnull=True, is_archived=False).order_by(
        "time_slot"
    ):
        practical_batches.append(_serialize_batch(batch))

    active_students = AdmittedStudent.objects.filter(is_archived=False, batch_status="active")
    total_students = active_students.count()
    students_with_theory = active_students.filter(theory_batch_time__isnull=False).exclude(theory_batch_time="").count()
    students_with_practical = (
        active_students.filter(practical_batch_time__isnull=False).exclude(practical_batch_time="").count()
    )

    return {
        "theory_batches": theory_batches,
        "practical_batches": practical_batches,
        "total_students": total_students,
        "students_with_theory": students_with_theory,
        "students_with_practical": students_with_practical,
        "students_without_batch": total_students - max(students_with_theory, students_with_practical),
    }


def _serialize_batch(batch):
    count_filter = (
        {"theory_batch_time": batch.time_slot}
        if batch.batch_type == "Theory"
        else {"practical_batch_time": batch.time_slot}
    )
    count = AdmittedStudent.objects.filter(is_archived=False, batch_status="active", **count_filter).count()
    return {
        "id": batch.id,
        "slot": batch.time_slot,
        "display": get_time_slot_display(batch.time_slot),
        "count": count,
        "capacity": batch.capacity,
        "utilization": round((count / batch.capacity) * 100, 2) if batch.capacity else 0,
    }


def get_batch_lifecycle_queryset(*, statuses=None, month="", year="", course="", search=""):
    queryset = (
        AdmittedStudent.objects.filter(is_archived=False)
        .exclude(batch_month__isnull=True)
        .exclude(batch_month="")
        .exclude(batch_year__isnull=True)
        .exclude(batch_year="")
    )

    if statuses:
        queryset = queryset.filter(batch_status__in=statuses)
    if month:
        queryset = queryset.filter(batch_month=month)
    if year:
        queryset = queryset.filter(batch_year=year)
    if course:
        queryset = queryset.filter(course=course)
    if search:
        queryset = queryset.filter(
            Q(batch_month__icontains=search) | Q(batch_year__icontains=search) | Q(course__icontains=search)
        )

    return queryset


def _summarize_grouped_batches(queryset):
    rows = (
        queryset.values("batch_month", "batch_year", "batch_status", "course")
        .annotate(
            student_count=Count("id"),
            total_fees=Sum("total_fees"),
            paid_fees=Sum("paid_fees"),
            admission_count=Count("id"),
        )
        .order_by("-batch_year", "batch_month", "course", "batch_status")
    )

    summaries = []
    for row in rows:
        total_fees = row["total_fees"] or Decimal("0.00")
        paid_fees = row["paid_fees"] or Decimal("0.00")
        course_name = row["course"] or "No course assigned"
        summaries.append(
            {
                "batch_month": row["batch_month"],
                "batch_year": row["batch_year"],
                "batch_status": row["batch_status"],
                "course": row["course"] or "",
                "course_name": course_name,
                "student_count": row["student_count"],
                "admission_count": row["admission_count"],
                "total_fees": total_fees,
                "paid_fees": paid_fees,
                "pending_fees": total_fees - paid_fees,
                "courses": [{"name": course_name, "count": row["student_count"]}],
                "course_names": course_name,
            }
        )
    return summaries


def get_active_batch_summaries(*, month="", year="", course="", search=""):
    queryset = get_batch_lifecycle_queryset(
        statuses=ACTIVE_BATCH_STATUSES, month=month, year=year, course=course, search=search
    )
    return _summarize_grouped_batches(queryset)


def get_ended_batch_summaries(*, month="", year="", course="", search=""):
    queryset = get_batch_lifecycle_queryset(
        statuses=ENDED_BATCH_STATUSES, month=month, year=year, course=course, search=search
    )
    return _summarize_grouped_batches(queryset)


def get_batch_transition_preview(*, batch_month, batch_year, course="", statuses=None):
    queryset = get_batch_lifecycle_queryset(statuses=statuses, month=batch_month, year=batch_year, course=course)
    students = queryset.select_related("batch_ended_by", "batch_restored_by")
    if not students.exists():
        raise ValueError("No students found for the selected batch.")

    active_count = students.filter(batch_status="active").count()
    total_students = students.count()
    total_fees = students.aggregate(total=Sum("total_fees"), paid=Sum("paid_fees"))
    earliest_admission = students.order_by("admission_date").values_list("admission_date", flat=True).first()
    latest_admission = students.order_by("-admission_date").values_list("admission_date", flat=True).first()
    attendance_taken = students.filter(attendance_records__isnull=False).distinct().count()

    return {
        "batch_month": batch_month,
        "batch_year": batch_year,
        "course": course,
        "student_count": total_students,
        "active_count": active_count,
        "courses": list(students.values_list("course", flat=True).distinct().order_by("course")),
        "total_fees": total_fees["total"] or Decimal("0.00"),
        "paid_fees": total_fees["paid"] or Decimal("0.00"),
        "pending_fees": (total_fees["total"] or Decimal("0.00")) - (total_fees["paid"] or Decimal("0.00")),
        "first_admission_date": earliest_admission,
        "last_admission_date": latest_admission,
        "attendance_marked_students": attendance_taken,
        "status_breakdown": {
            row["batch_status"]: row["count"] for row in students.values("batch_status").annotate(count=Count("id"))
        },
    }


def _validate_transition(students, transition_key):
    config = ADMIN_MUTATION_STATUSES[transition_key]
    invalid = students.exclude(batch_status__in=config["from"])
    if invalid.exists():
        statuses = ", ".join(sorted(set(invalid.values_list("batch_status", flat=True))))
        raise ValueError(f"Batch transition is not allowed for students currently marked as: {statuses}.")


@transaction.atomic
def update_batch_lifecycle(
    *, batch_month, batch_year, course="", action, actor=None, request=None, remarks="", override=False
):
    if action not in ADMIN_MUTATION_STATUSES:
        raise ValueError("Unsupported batch lifecycle action.")

    students = AdmittedStudent.objects.select_for_update().filter(
        is_archived=False,
        batch_month=batch_month,
        batch_year=batch_year,
    )
    if course:
        students = students.filter(course=course)
    if not students.exists():
        raise ValueError("No students found for the selected batch.")

    _validate_transition(students, action)
    preview = get_batch_transition_preview(batch_month=batch_month, batch_year=batch_year, course=course)

    if action == "end" and preview["pending_fees"] > 0 and not override:
        raise ValueError("Pending fees exist for this batch. Use admin override to complete the batch.")

    update_kwargs = {
        "batch_status": ADMIN_MUTATION_STATUSES[action]["to"],
        "updated_at": timezone.now(),
    }
    today = date.today()

    if action == "end":
        update_kwargs.update(
            {
                "batch_end_date": today,
                "batch_ended_by_id": actor.pk if getattr(actor, "is_authenticated", False) else None,
            }
        )
    elif action == "restore":
        update_kwargs.update(
            {
                "batch_restored_date": today,
                "batch_restored_by_id": actor.pk if getattr(actor, "is_authenticated", False) else None,
                "batch_end_date": None,
            }
        )

    affected = students.update(**update_kwargs)
    BatchActionLog.objects.create(
        batch_month=batch_month,
        batch_year=batch_year,
        action_type=ADMIN_MUTATION_STATUSES[action]["log"],
        action_by=actor if getattr(actor, "is_authenticated", False) else None,
        affected_students_count=affected,
        remarks=remarks or "",
    )
    log_audit_event(
        action=f"batch.lifecycle_{ADMIN_MUTATION_STATUSES[action]['log']}",
        actor=actor,
        request=request,
        metadata={
            "batch_month": batch_month,
            "batch_year": batch_year,
            "course": course,
            "affected_students_count": affected,
            "override": override,
            "remarks": remarks or "",
        },
    )
    return affected


def get_batch_report_data(*, month="", year="", course="", status=""):
    statuses = [status] if status else None
    queryset = get_batch_lifecycle_queryset(statuses=statuses, month=month, year=year, course=course)
    summaries = _summarize_grouped_batches(queryset)
    action_logs = BatchActionLog.objects.all().select_related("action_by")

    revenue_by_batch = []
    for summary in summaries:
        revenue_by_batch.append(
            {
                "batch": f"{summary['batch_month']} {summary['batch_year']}",
                "status": summary["batch_status"],
                "student_count": summary["student_count"],
                "paid_fees": summary["paid_fees"],
                "pending_fees": summary["pending_fees"],
                "courses": summary["course_names"],
            }
        )

    total_students = queryset.count()
    completed_students = queryset.filter(batch_status="completed").count()
    cancelled_students = queryset.filter(batch_status="cancelled").count()
    archived_students = queryset.filter(batch_status="archived").count()
    fee_revenue = FeePayment.objects.filter(student__in=queryset).aggregate(total=Sum("amount"))["total"] or Decimal(
        "0.00"
    )

    return {
        "summaries": summaries,
        "revenue_by_batch": revenue_by_batch,
        "action_logs": action_logs[:50],
        "stats": {
            "total_students": total_students,
            "active_students": queryset.filter(batch_status="active").count(),
            "completed_students": completed_students,
            "cancelled_students": cancelled_students,
            "archived_students": archived_students,
            "completion_rate": round((completed_students / total_students) * 100, 2) if total_students else 0,
            "fee_revenue": fee_revenue,
        },
    }


@transaction.atomic
def create_batch(*, batch_type, time_slot, capacity=50, actor=None, request=None):
    batch = Batch.objects.create(
        batch_type=batch_type,
        time_slot=time_slot,
        capacity=capacity,
    )
    log_audit_event(
        action="batch.created",
        actor=actor,
        target=batch,
        request=request,
        metadata={"time_slot": time_slot, "batch_type": batch_type},
    )
    return batch


@transaction.atomic
def archive_batch(*, batch, actor=None, request=None):
    if batch.batch_type == "Theory":
        AdmittedStudent.objects.filter(
            theory_batch_time=batch.time_slot, is_archived=False, batch_status="active"
        ).update(theory_batch_time=None)
    else:
        AdmittedStudent.objects.filter(
            practical_batch_time=batch.time_slot, is_archived=False, batch_status="active"
        ).update(practical_batch_time=None)

    batch.is_archived = True
    batch.save(update_fields=["is_archived", "updated_at"])
    log_audit_event(
        action="batch.archived",
        actor=actor,
        target=batch,
        request=request,
        metadata={"time_slot": batch.time_slot, "batch_type": batch.batch_type},
    )
    return batch
