from datetime import date as current_date
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F, Prefetch, Q
from django.shortcuts import redirect, render

from core.constants import TIME_SLOT_CHOICES, TIME_SLOT_DISPLAY_MAP
from core.models import AdmittedStudent, Attendance, Batch
from core.permissions import roles_required


def _unique_time_slots(slot_values):
    seen = set()
    slots_by_value = {slot: TIME_SLOT_DISPLAY_MAP.get(slot, slot) for slot in slot_values if slot}
    ordered_slots = []

    for slot, display in TIME_SLOT_CHOICES:
        if slot in slots_by_value and slot not in seen:
            ordered_slots.append((slot, display))
            seen.add(slot)

    for slot, display in sorted(slots_by_value.items(), key=lambda item: item[1]):
        if slot not in seen:
            ordered_slots.append((slot, display))
            seen.add(slot)

    return ordered_slots


@login_required
@roles_required("Super Admin", "Admin", "Attendance Manager")
def mark_attendance_page(request):
    if request.method == "POST":
        attendance_date = request.POST.get("attendance_date")
        batch_time = request.POST.get("batch_time")
        batch_type = request.POST.get("batch_type")
        if not all([attendance_date, batch_time, batch_type]):
            messages.error(request, "Please select date, batch time, and batch type.")
            return redirect("mark_attendance")
        return redirect("save_attendance", date=attendance_date, batch_time=batch_time, batch_type=batch_type)

    active_students = AdmittedStudent.objects.filter(is_archived=False, batch_status="active")
    theory_slot_values = (
        active_students.exclude(theory_batch_time__isnull=True)
        .exclude(theory_batch_time="")
        .values_list("theory_batch_time", flat=True)
        .distinct()
    )
    practical_slot_values = (
        active_students.exclude(practical_batch_time__isnull=True)
        .exclude(practical_batch_time="")
        .values_list("practical_batch_time", flat=True)
        .distinct()
    )
    theory_slots = _unique_time_slots(theory_slot_values)
    practical_slots = _unique_time_slots(practical_slot_values)
    return render(
        request,
        "core/timetable/mark_attendance.html",
        {
            "theory_slots": theory_slots,
            "practical_slots": practical_slots,
            "today": current_date.today().isoformat(),
            "active_page": "mark_attendance",
        },
    )


@login_required
@roles_required("Super Admin", "Admin", "Attendance Manager")
def save_attendance(request, date, batch_time, batch_type):
    try:
        attendance_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        messages.error(request, "Invalid attendance date.")
        return redirect("mark_attendance")

    filter_kwargs = {"theory_batch_time": batch_time} if batch_type == "theory" else {"practical_batch_time": batch_time}
    students = AdmittedStudent.objects.filter(is_archived=False, batch_status="active", **filter_kwargs).order_by("full_name")

    if request.method == "POST":
        with transaction.atomic():
            for student in students:
                status = request.POST.get(f"attendance_{student.id}", "A")
                remarks = request.POST.get(f"remarks_{student.id}", "").strip()
                attendance, created = Attendance.objects.get_or_create(
                    student=student,
                    date=attendance_date,
                    defaults={"marked_by": request.user, "theory_attendance": "", "practical_attendance": ""},
                )
                if batch_type == "theory":
                    attendance.theory_attendance = status
                    if created:
                        attendance.practical_attendance = ""
                else:
                    attendance.practical_attendance = status
                    if created:
                        attendance.theory_attendance = ""
                attendance.remarks = remarks or attendance.remarks
                attendance.marked_by = request.user
                attendance.save()

        messages.success(request, f"Attendance saved for {batch_type} batch on {attendance_date}.")
        return redirect("attendance_reports")

    return render(
        request,
        "core/timetable/save_attendance.html",
        {
            "students": students,
            "attendance_date": attendance_date,
            "batch_time": batch_time,
            "time_slot_display": TIME_SLOT_DISPLAY_MAP.get(batch_time, batch_time),
            "batch_type": batch_type,
            "status_choices": [("P", "Present"), ("A", "Absent"), ("L", "Leave"), ("H", "Holiday")],
            "active_page": "mark_attendance",
        },
    )


@login_required
@roles_required("Super Admin", "Admin", "Attendance Manager", "Counselor")
def attendance_reports(request):
    report_type = request.GET.get("report_type", "student")

    if report_type == "daily":
        return redirect("attendance_reports")

    if report_type == "batch":
        selected_date = request.GET.get("date")
        report_date = datetime.strptime(selected_date, "%Y-%m-%d").date() if selected_date else current_date.today()
        theory_slots = Batch.objects.filter(batch_type="Theory", course__isnull=True, is_archived=False).values_list("time_slot", flat=True).distinct()
        practical_slots = Batch.objects.filter(batch_type="Practical", course__isnull=True, is_archived=False).values_list("time_slot", flat=True).distinct()
        all_slots = sorted(set(theory_slots) | set(practical_slots))
        attendance_records = Attendance.objects.filter(date=report_date).select_related("student")
        attendance_by_student_id = {record.student_id: record for record in attendance_records}
        batch_reports = []

        def serialize_batch_students(students, attendance_type):
            serialized = []
            for student in students.order_by("full_name"):
                attendance_record = attendance_by_student_id.get(student.id)
                status = "A"
                if attendance_record:
                    status = attendance_record.theory_attendance or "A" if attendance_type == "theory" else attendance_record.practical_attendance or "A"
                serialized.append(
                    {
                        "id": student.id,
                        "full_name": student.full_name,
                        "mobile_own": student.mobile_own,
                        "status": status,
                    }
                )
            return serialized

        for slot in all_slots:
            theory_students = AdmittedStudent.objects.filter(is_archived=False, theory_batch_time=slot)
            practical_students = AdmittedStudent.objects.filter(is_archived=False, practical_batch_time=slot)
            theory_present = attendance_records.filter(student__in=theory_students, theory_attendance="P").count()
            practical_present = attendance_records.filter(student__in=practical_students, practical_attendance="P").count()
            batch_reports.append(
                {
                    "slot": slot,
                    "display": TIME_SLOT_DISPLAY_MAP.get(slot, slot),
                    "theory": {
                        "total": theory_students.count(),
                        "present": theory_present,
                        "absent": theory_students.count() - theory_present,
                        "students": serialize_batch_students(theory_students, "theory"),
                    },
                    "practical": {
                        "total": practical_students.count(),
                        "present": practical_present,
                        "absent": practical_students.count() - practical_present,
                        "students": serialize_batch_students(practical_students, "practical"),
                    },
                }
            )

        return render(
            request,
            "core/timetable/attendance_reports.html",
            {
                "report_type": "batch",
                "report_date": report_date,
                "batch_reports": batch_reports,
                "title": f"Batch Attendance Report - {report_date}",
                "active_page": "attendance_reports",
            },
        )

    selected_batch = request.GET.get("batch", "").strip()
    selected_theory_time = request.GET.get("theory_time", "").strip()
    selected_practical_time = request.GET.get("practical_time", "").strip()
    sort_by = request.GET.get("sort", "name").strip()
    all_students = AdmittedStudent.objects.filter(is_archived=False)
    available_batches = sorted(
        {
            student.batch_display
            for student in all_students.only("batch_month", "batch_year")
            if student.batch_display != "Not Assigned"
        }
    )
    available_theory_times = [
        (slot, TIME_SLOT_DISPLAY_MAP.get(slot, slot))
        for slot in all_students.exclude(theory_batch_time__isnull=True)
        .exclude(theory_batch_time="")
        .order_by("theory_batch_time")
        .values_list("theory_batch_time", flat=True)
        .distinct()
    ]
    available_practical_times = [
        (slot, TIME_SLOT_DISPLAY_MAP.get(slot, slot))
        for slot in all_students.exclude(practical_batch_time__isnull=True)
        .exclude(practical_batch_time="")
        .order_by("practical_batch_time")
        .values_list("practical_batch_time", flat=True)
        .distinct()
    ]

    students_queryset = all_students
    if selected_batch == "Not Assigned":
        students_queryset = students_queryset.filter(
            Q(batch_month__isnull=True) | Q(batch_month="") | Q(batch_year__isnull=True) | Q(batch_year="")
        )
    elif selected_batch:
        batch_parts = selected_batch.rsplit(" ", 1)
        if len(batch_parts) == 2:
            students_queryset = students_queryset.filter(batch_month=batch_parts[0], batch_year=batch_parts[1])

    if selected_theory_time:
        students_queryset = students_queryset.filter(theory_batch_time=selected_theory_time)

    if selected_practical_time:
        students_queryset = students_queryset.filter(practical_batch_time=selected_practical_time)

    if sort_by == "batch":
        students_queryset = students_queryset.order_by("batch_year", "batch_month", "full_name")
    elif sort_by == "theory_time":
        students_queryset = students_queryset.order_by("theory_batch_time", "full_name")
    elif sort_by == "practical_time":
        students_queryset = students_queryset.order_by("practical_batch_time", "full_name")
    elif sort_by == "fees_pending":
        students_queryset = students_queryset.annotate(balance_fees=F("total_fees") - F("paid_fees")).order_by(
            "-balance_fees", "full_name"
        )
    else:
        students_queryset = students_queryset.order_by("full_name")

    students = students_queryset.prefetch_related(
        Prefetch("attendance_records", queryset=Attendance.objects.order_by("date"))
    )
    attendance_dates = list(Attendance.objects.order_by("date").values_list("date", flat=True).distinct())
    student_reports = []

    for student in students:
        attendance_records = list(student.attendance_records.all())
        total_records = len(attendance_records)
        present_count = sum(1 for record in attendance_records if record.theory_attendance == "P" or record.practical_attendance == "P")
        absent_count = sum(1 for record in attendance_records if record.theory_attendance == "A" and record.practical_attendance == "A")
        attendance_by_date = {record.date: record for record in attendance_records}
        attendance_pairs = []
        for date_value in attendance_dates:
            record = attendance_by_date.get(date_value)
            attendance_pairs.append(
                {
                    "date": date_value,
                    "theory_status": record.theory_attendance if record else "",
                    "practical_status": record.practical_attendance if record else "",
                }
            )
        student_reports.append(
            {
                "student": student,
                "mobile_no": student.mobile_own,
                "has_fee_balance": student.remaining_fees > 0,
                "remaining_fees": student.remaining_fees,
                "total": total_records,
                "present": present_count,
                "absent": absent_count,
                "theory_present": sum(1 for record in attendance_records if record.theory_attendance == "P"),
                "theory_absent": sum(1 for record in attendance_records if record.theory_attendance == "A"),
                "practical_present": sum(1 for record in attendance_records if record.practical_attendance == "P"),
                "practical_absent": sum(1 for record in attendance_records if record.practical_attendance == "A"),
                "records": attendance_records,
                "attendance_pairs": attendance_pairs,
                "theory_days": [{"date": date_value, "status": (attendance_by_date.get(date_value).theory_attendance if attendance_by_date.get(date_value) else "")} for date_value in attendance_dates],
                "practical_days": [{"date": date_value, "status": (attendance_by_date.get(date_value).practical_attendance if attendance_by_date.get(date_value) else "")} for date_value in attendance_dates],
                "percentage": round((present_count / total_records) * 100, 2) if total_records else 0,
            }
        )

    return render(
        request,
        "core/timetable/attendance_reports.html",
        {
            "report_type": "student",
            "student_reports": student_reports,
            "attendance_dates": attendance_dates,
            "attendance_colspan": (len(attendance_dates) * 2) + 3,
            "available_batches": available_batches,
            "available_theory_times": available_theory_times,
            "available_practical_times": available_practical_times,
            "selected_batch": selected_batch,
            "selected_theory_time": selected_theory_time,
            "selected_practical_time": selected_practical_time,
            "sort_by": sort_by,
            "title": "Student Attendance Report",
            "active_page": "attendance_reports",
        },
    )
