from datetime import date

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from core.models import AdmittedStudent, Attendance, AuditLog, Batch, BatchActionLog, FeePayment, LoginAttempt, StudentFinanceDetail
from core.permissions import ROLE_ADMIN, ROLE_ATTENDANCE_MANAGER, ensure_role_groups


@override_settings(ROOT_URLCONF="Project.urls")
class ERPFoundationTests(TestCase):
    def setUp(self):
        ensure_role_groups()
        self.client = Client()
        self.user = User.objects.create_user(username="staffuser", password="StrongPass123")

    def test_new_admission_generates_student_id_and_audit_log(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("new_admission"),
            {
                "course": "MS-CIT",
                "student_name": "Asha",
                "father_name": "Ramesh",
                "surname": "Patil",
                "mother_name": "Sita",
                "date_of_birth": "2004-06-15",
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
                "batch_month": "",
                "batch_year": "",
                "theory_batch_time": "",
                "practical_batch_time": "",
                "total_fees": "5000.00",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        student = AdmittedStudent.objects.get(student_name="Asha")
        self.assertTrue(student.student_id.startswith("SSC2026"))
        self.assertTrue(AuditLog.objects.filter(action="admission.created", object_id=str(student.pk)).exists())

    def test_fee_payment_updates_paid_fees_and_installments(self):
        self.client.force_login(self.user)
        student = AdmittedStudent.objects.create(
            course="MS-CIT",
            student_name="Vijay",
            father_name="Anil",
            surname="Patel",
            mother_name="Uma",
            date_of_birth=date(2003, 2, 10),
            mobile_own="9123456789",
            parent_mobile="9234567890",
            gender="Male",
            marital_status="Single",
            address="Address",
            city="Nashik",
            tehsil_block="Nashik",
            district="Nashik",
            pin_code="422001",
            educational_qualification="Graduate",
            total_fees="6000.00",
            admission_date=date(2026, 5, 1),
        )

        response = self.client.post(
            reverse("submit_fee_payment"),
            {
                "student_id": student.id,
                "amount": "1500.00",
                "payment_mode": "Cash",
                "payment_date": "2026-05-02",
                "remarks": "First installment",
            },
        )

        self.assertEqual(response.status_code, 200)
        student.refresh_from_db()
        finance_detail = StudentFinanceDetail.objects.get(student=student)
        self.assertEqual(str(student.paid_fees), "1500.00")
        self.assertEqual(str(finance_detail.first_installment), "1500.00")
        self.assertTrue(AuditLog.objects.filter(action="fees.payment_recorded").exists())

    def test_batch_overview_requires_role(self):
        Batch.objects.create(batch_type="Theory", time_slot="08:00-09:00", capacity=30)

        self.client.force_login(self.user)
        response = self.client.get(reverse("batch_overview"))
        self.assertEqual(response.status_code, 302)

        attendance_group = Group.objects.get(name=ROLE_ATTENDANCE_MANAGER)
        self.user.groups.add(attendance_group)
        response = self.client.get(reverse("batch_overview"))
        self.assertEqual(response.status_code, 200)

    @override_settings(LOGIN_FAILURE_LIMIT=2, LOGIN_FAILURE_WINDOW=60)
    def test_login_throttling_blocks_after_repeated_failures(self):
        self.client.logout()

        response = self.client.post(reverse("login"), {"username": "staffuser", "password": "wrongpass"})
        self.assertEqual(response.status_code, 401)
        response = self.client.post(reverse("login"), {"username": "staffuser", "password": "wrongpass"})
        self.assertEqual(response.status_code, 401)
        response = self.client.post(reverse("login"), {"username": "staffuser", "password": "wrongpass"})
        self.assertEqual(response.status_code, 429)
        self.assertGreaterEqual(LoginAttempt.objects.filter(username="staffuser", successful=False).count(), 3)

    def test_end_batch_hides_students_from_daily_attendance_without_data_loss(self):
        admin_group = Group.objects.get(name=ROLE_ADMIN)
        self.user.groups.add(admin_group)
        self.client.force_login(self.user)

        student = AdmittedStudent.objects.create(
            course="MS-CIT",
            student_name="Batch",
            father_name="Student",
            surname="Active",
            mother_name="Parent",
            date_of_birth=date(2004, 1, 1),
            mobile_own="9988776655",
            parent_mobile="9988776654",
            gender="Male",
            marital_status="Single",
            address="Address",
            city="Pune",
            tehsil_block="Haveli",
            district="Pune",
            pin_code="411001",
            educational_qualification="Graduate",
            total_fees="5000.00",
            paid_fees="5000.00",
            admission_date=date(2026, 1, 10),
            batch_month="January",
            batch_year="2026",
            theory_batch_time="08:00-09:00",
            practical_batch_time="09:00-10:00",
        )
        FeePayment.objects.create(
            student=student,
            amount="5000.00",
            payment_mode="Cash",
            payment_date=date(2026, 1, 15),
            total_fees_at_payment="5000.00",
            paid_before_this="0.00",
            remaining_after_this="0.00",
        )
        Attendance.objects.create(student=student, date=date(2026, 2, 1), theory_attendance="P", practical_attendance="A", marked_by=self.user)

        response = self.client.post(
            reverse("end_batch_confirm"),
            {
                "batch_month": "January",
                "batch_year": "2026",
                "remarks": "Course completed",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        student.refresh_from_db()
        self.assertEqual(student.batch_status, "completed")
        self.assertIsNotNone(student.batch_end_date)
        self.assertTrue(FeePayment.objects.filter(student=student).exists())
        self.assertTrue(Attendance.objects.filter(student=student).exists())
        self.assertTrue(AdmittedStudent.objects.filter(pk=student.pk).exists())
        self.assertFalse(
            AdmittedStudent.objects.filter(batch_status="active", theory_batch_time="08:00-09:00", pk=student.pk).exists()
        )
        self.assertTrue(BatchActionLog.objects.filter(batch_month="January", batch_year="2026", action_type="ended").exists())

    def test_restore_batch_returns_students_to_attendance_eligibility(self):
        admin_group = Group.objects.get(name=ROLE_ADMIN)
        self.user.groups.add(admin_group)
        self.client.force_login(self.user)

        student = AdmittedStudent.objects.create(
            course="MS-CIT",
            student_name="Restore",
            father_name="Student",
            surname="Batch",
            mother_name="Parent",
            date_of_birth=date(2004, 1, 1),
            mobile_own="9988776644",
            parent_mobile="9988776643",
            gender="Female",
            marital_status="Single",
            address="Address",
            city="Pune",
            tehsil_block="Haveli",
            district="Pune",
            pin_code="411001",
            educational_qualification="Graduate",
            total_fees="5000.00",
            paid_fees="5000.00",
            admission_date=date(2026, 1, 10),
            batch_month="February",
            batch_year="2026",
            batch_status="completed",
            batch_end_date=date(2026, 4, 30),
            theory_batch_time="08:00-09:00",
        )

        response = self.client.post(
            reverse("restore_batch_confirm"),
            {
                "batch_month": "February",
                "batch_year": "2026",
                "remarks": "Reopened for exam retake",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        student.refresh_from_db()
        self.assertEqual(student.batch_status, "active")
        self.assertIsNotNone(student.batch_restored_date)
        self.assertTrue(
            AdmittedStudent.objects.filter(batch_status="active", theory_batch_time="08:00-09:00", pk=student.pk).exists()
        )
        self.assertTrue(BatchActionLog.objects.filter(batch_month="February", batch_year="2026", action_type="restored").exists())

    def test_unauthorized_user_cannot_end_batch(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("end_batch"))
        self.assertEqual(response.status_code, 302)
