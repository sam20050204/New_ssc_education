from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from core.forms import AdmittedStudentForm
from core.models import Course
from core.services.admission_service import create_admission


@login_required
def new_admission(request):
    enquiry_data = request.session.get("enquiry_conversion", {})

    if request.method == "POST":
        form = AdmittedStudentForm(request.POST, request.FILES)
        if form.is_valid():
            admission = create_admission(form=form, actor=request.user, request=request)
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
