from django.db import transaction

from core.audit_logs import log_audit_event
from core.models import AdmittedStudent
from core.utils import invalidate_admission_cache


@transaction.atomic
def create_admission(*, form, actor=None, request=None):
    admission = form.save(commit=False)
    admission.save()
    invalidate_admission_cache()
    log_audit_event(
        action="admission.created",
        actor=actor,
        target=admission,
        request=request,
        metadata={
            "course": admission.course,
            "student_id": admission.student_id,
        },
    )

    from core.services.whatsapp_service import send_admission_notification
    transaction.on_commit(lambda: send_admission_notification(admission))

    return admission


def get_active_students_queryset():
    return AdmittedStudent.objects.filter(is_archived=False)
