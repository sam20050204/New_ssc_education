from datetime import date
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from core.models import AdmittedStudent, Attendance, AuditLog, Enquiry
from core.permissions import ROLE_ADMIN, ROLE_ATTENDANCE_MANAGER, ensure_role_groups
from core.validators import validate_filename, validate_image_file


@override_settings(ROOT_URLCONF="Project.urls")
class ExtendedWorkflowTests(TestCase):
    def setUp(self):
        ensure_role_groups()
        self.client = Client()
        self.user = User.objects.create_user(username="staff", password="Pass1234")
        self.client.force_login(self.user)

    def _make_student(self, **overrides):
        payload = {
            "course": "MS-CIT",
            "student_name": "Asha",
            "father_name": "Ramesh",
            "surname": "Patil",
            "mother_name": "Sita",
            "date_of_birth": date(2004, 6, 15),
            "mobile_own": "9876543210",
            "parent_mobile": "9876543211",
            "gender": "Female",
            "marital_status": "Single",
            "address": "Main Road",
            "city": "Pune",
            "tehsil_block": "Haveli",
            "district": "Pune",
            "pin_code": "411001",
            "educational_qualification": "HSC",
            "total_fees": Decimal("5000.00"),
            "paid_fees": Decimal("0.00"),
            "admission_date": date(2026, 5, 1),
        }
        payload.update(overrides)
        return AdmittedStudent.objects.create(**payload)

    def test_create_enquiry_saves_to_db(self):
        response = self.client.post(
            reverse("enquiry_list"),
            {
                "name": "Leena Patil",
                "mobile": "9876501234",
                "education": "Graduate",
                "course": "MS-CIT",
                "address": "Market Road",
                "city": "Pune",
                "taluka": "Haveli",
                "district": "Pune",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Enquiry.objects.count(), 1)
        self.assertEqual(Enquiry.objects.get().name, "Leena Patil")

    def test_fee_overpayment_is_rejected(self):
        student = self._make_student(paid_fees=Decimal("5000.00"))

        response = self.client.post(
            reverse("submit_fee_payment"),
            {
                "student_id": student.id,
                "amount": "1000.00",
                "payment_mode": "Cash",
                "payment_date": "2026-05-02",
                "remarks": "Overpayment attempt",
            },
        )

        self.assertEqual(response.status_code, 400)
        student.refresh_from_db()
        self.assertEqual(student.paid_fees, Decimal("5000.00"))

    def test_partial_payment_updates_remaining_fees_and_audit_log(self):
        student = self._make_student(total_fees=Decimal("6000.00"))

        response = self.client.post(
            reverse("submit_fee_payment"),
            {
                "student_id": student.id,
                "amount": "2000.00",
                "payment_mode": "Cash",
                "payment_date": "2026-05-02",
                "remarks": "First installment",
            },
        )

        self.assertEqual(response.status_code, 200)
        student.refresh_from_db()
        self.assertEqual(student.paid_fees, Decimal("2000.00"))
        self.assertEqual(student.remaining_fees, Decimal("4000.00"))
        self.assertTrue(AuditLog.objects.filter(action="fees.payment_recorded").exists())

    def test_mark_attendance_saves_record(self):
        attendance_group = Group.objects.get(name=ROLE_ATTENDANCE_MANAGER)
        self.user.groups.add(attendance_group)
        student = self._make_student(theory_batch_time="08:00-09:00")

        response = self.client.post(
            reverse("save_attendance", args=["2026-05-03", "08:00-09:00", "theory"]),
            {
                f"attendance_{student.id}": "P",
                f"remarks_{student.id}": "On time",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Attendance.objects.filter(student=student, date=date(2026, 5, 3)).exists())

    def test_duplicate_attendance_for_same_date_is_not_duplicated(self):
        attendance_group = Group.objects.get(name=ROLE_ATTENDANCE_MANAGER)
        self.user.groups.add(attendance_group)
        student = self._make_student(theory_batch_time="08:00-09:00")
        target_url = reverse("save_attendance", args=["2026-05-04", "08:00-09:00", "theory"])

        self.client.post(target_url, {f"attendance_{student.id}": "P"})
        self.client.post(target_url, {f"attendance_{student.id}": "A"})

        self.assertEqual(Attendance.objects.filter(student=student, date=date(2026, 5, 4)).count(), 1)

    def test_unauthenticated_user_is_redirected_from_dashboard(self):
        self.client.logout()
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_non_admin_cannot_access_sales_dashboard(self):
        response = self.client.get(reverse("sales_services_dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_admin_can_access_sales_dashboard(self):
        admin_group = Group.objects.get(name=ROLE_ADMIN)
        self.user.groups.add(admin_group)
        response = self.client.get(reverse("sales_services_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_update_student_city_persists_and_creates_audit_log(self):
        student = self._make_student(city="Pune")

        response = self.client.post(
            reverse("update_student_admitted", args=[student.id]),
            {
                "city": "Mumbai",
            },
        )

        self.assertEqual(response.status_code, 200)
        student.refresh_from_db()
        self.assertEqual(student.city, "Mumbai")
        self.assertTrue(AuditLog.objects.filter(action="student.updated", object_id=str(student.pk)).exists())

    def test_admin_login_uses_custom_admin_path(self):
        self.assertEqual(reverse("admin:login"), "/secure-admin/login/")

    def test_validate_filename_blocks_path_traversal(self):
        with self.assertRaises(ValidationError):
            validate_filename("../etc/passwd")
        with self.assertRaises(ValidationError):
            validate_filename("/absolute/path")

    def test_validate_image_file_blocks_wrong_extension(self):
        bad_file = SimpleUploadedFile("payload.exe", b"not-an-image", content_type="application/octet-stream")
        with self.assertRaises(ValidationError):
            validate_image_file(bad_file)
