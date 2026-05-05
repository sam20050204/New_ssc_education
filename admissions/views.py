from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from core.forms import AdmittedStudentForm
from core.models import Course
from core.services.admission_service import create_admission
from core.services.collaboration_service import create_role_notification


@login_required
def new_admission(request):
    enquiry_data = request.session.get("enquiry_conversion", {})

    if request.method == "POST":
        form = AdmittedStudentForm(request.POST, request.FILES)
        if form.is_valid():
            admission = create_admission(form=form, actor=request.user, request=request)
            create_role_notification(
                role_key="admin",
                category="admissions",
                priority="success",
                event_key="admissions.student.created",
                title="New admission confirmed",
                message=f"{admission.full_name} was admitted to {admission.custom_course if admission.course == 'Other' and admission.custom_course else admission.course}.",
                actor=request.user,
                link_url="/admission/list/",
                action_label="Review Student",
                content_object=admission,
            )
            create_role_notification(
                role_key="accountant",
                category="financial",
                priority="pending",
                event_key="financial.student.onboarded",
                title="New student added for fee tracking",
                message=f"{admission.full_name} is ready for payment tracking with total fees Rs. {admission.total_fees}.",
                actor=request.user,
                link_url="/payment-tracking/",
                action_label="Open Tracking",
                content_object=admission,
            )
            request.session.pop("enquiry_conversion", None)
            messages.success(
                request,
                f"Admission recorded for {admission.full_name} with student ID {admission.student_id}.",
            )
            return redirect("new_admission")

        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    else:
        form = AdmittedStudentForm()

    return render(
        request,
        "core/new_admission.html",
        {
            "active_page": "new_admission",
            "form": form,
            "enquiry_data": enquiry_data,
            "all_courses": Course.objects.order_by("name"),
        },
    )
