from datetime import date

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from core.models import AdmittedStudent
from core.permissions import ROLE_ATTENDANCE_MANAGER, ensure_role_groups


@override_settings(ROOT_URLCONF="Project.urls")
class AttendanceViewTests(TestCase):
    def setUp(self):
        ensure_role_groups()
        self.client = Client()
        self.user = User.objects.create_user(username="staffuser", password="StrongPass123")
        self.user.groups.add(Group.objects.get(name=ROLE_ATTENDANCE_MANAGER))
        self.client.force_login(self.user)

    def test_mark_attendance_shows_unique_batch_times(self):
        for index in range(2):
            AdmittedStudent.objects.create(
                course="MS-CIT",
                student_name=f"Student{index}",
                father_name="Parent",
                surname="Test",
                mother_name="Mother",
                date_of_birth=date(2004, 1, 1),
                mobile_own=f"998877665{index}",
                parent_mobile=f"887766554{index}",
                gender="Male",
                marital_status="Single",
                address="Address",
                city="Pune",
                tehsil_block="Haveli",
                district="Pune",
                pin_code="411001",
                educational_qualification="HSC",
                batch_status="active",
                theory_batch_time="10:00-11:00",
                practical_batch_time="16:00-17:00",
                total_fees="5000.00",
                admission_date=date(2026, 5, 1),
            )

        response = self.client.get(reverse("mark_attendance"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["theory_slots"], [("10:00-11:00", "10:00 AM - 11:00 AM")])
        self.assertEqual(response.context["practical_slots"], [("16:00-17:00", "4:00 PM - 5:00 PM")])
