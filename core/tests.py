from datetime import date

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from core.models import (
    AdmittedStudent,
    Attendance,
    AuditLog,
    Batch,
    BatchActionLog,
    FeePayment,
    LoginAttempt,
    StudentFinanceDetail,
)
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
        Attendance.objects.create(
            student=student, date=date(2026, 2, 1), theory_attendance="P", practical_attendance="A", marked_by=self.user
        )

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
            AdmittedStudent.objects.filter(
                batch_status="active", theory_batch_time="08:00-09:00", pk=student.pk
            ).exists()
        )
        self.assertTrue(
            BatchActionLog.objects.filter(batch_month="January", batch_year="2026", action_type="ended").exists()
        )

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
            AdmittedStudent.objects.filter(
                batch_status="active", theory_batch_time="08:00-09:00", pk=student.pk
            ).exists()
        )
        self.assertTrue(
            BatchActionLog.objects.filter(batch_month="February", batch_year="2026", action_type="restored").exists()
        )

    def test_batch_students_endpoint_excludes_ended_students(self):
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        self.client.force_login(self.user)

        active_student = AdmittedStudent.objects.create(
            course="MS-CIT",
            student_name="Active",
            father_name="Student",
            surname="Batch",
            mother_name="Parent",
            date_of_birth=date(2004, 1, 1),
            mobile_own="9988776601",
            parent_mobile="9988776602",
            gender="Male",
            marital_status="Single",
            address="Address",
            city="Pune",
            tehsil_block="Haveli",
            district="Pune",
            pin_code="411001",
            educational_qualification="Graduate",
            batch_month="March",
            batch_year="2026",
            theory_batch_time="08:00-09:00",
        )
        AdmittedStudent.objects.create(
            course="MS-CIT",
            student_name="Ended",
            father_name="Student",
            surname="Batch",
            mother_name="Parent",
            date_of_birth=date(2004, 1, 1),
            mobile_own="9988776603",
            parent_mobile="9988776604",
            gender="Female",
            marital_status="Single",
            address="Address",
            city="Pune",
            tehsil_block="Haveli",
            district="Pune",
            pin_code="411001",
            educational_qualification="Graduate",
            batch_month="March",
            batch_year="2026",
            batch_status="completed",
            theory_batch_time="08:00-09:00",
        )

        response = self.client.get(
            reverse("get_batch_students"),
            {"batch_type": "Theory", "time_slot": "08:00-09:00"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(len(payload["students"]), 1)
        self.assertEqual(payload["students"][0]["id"], active_student.id)

    def test_batch_list_endpoint_counts_only_active_students(self):
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        self.client.force_login(self.user)

        Batch.objects.create(batch_type="Theory", time_slot="08:00-09:00", capacity=1)
        AdmittedStudent.objects.create(
            course="MS-CIT",
            student_name="Active",
            father_name="Student",
            surname="One",
            mother_name="Parent",
            date_of_birth=date(2004, 1, 1),
            mobile_own="9988776610",
            parent_mobile="9988776611",
            gender="Male",
            marital_status="Single",
            address="Address",
            city="Pune",
            tehsil_block="Haveli",
            district="Pune",
            pin_code="411001",
            educational_qualification="Graduate",
            theory_batch_time="08:00-09:00",
        )
        AdmittedStudent.objects.create(
            course="MS-CIT",
            student_name="Ended",
            father_name="Student",
            surname="Two",
            mother_name="Parent",
            date_of_birth=date(2004, 1, 1),
            mobile_own="9988776612",
            parent_mobile="9988776613",
            gender="Female",
            marital_status="Single",
            address="Address",
            city="Pune",
            tehsil_block="Haveli",
            district="Pune",
            pin_code="411001",
            educational_qualification="Graduate",
            batch_status="completed",
            theory_batch_time="08:00-09:00",
        )

        response = self.client.get(reverse("get_batch_list"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["total_students"], 1)
        self.assertEqual(payload["students_with_theory"], 1)
        self.assertEqual(payload["theory_batches"][0]["count"], 1)

    def test_batch_assignment_rejects_over_capacity(self):
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        self.client.force_login(self.user)

        Batch.objects.create(batch_type="Theory", time_slot="08:00-09:00", capacity=1)
        AdmittedStudent.objects.create(
            course="MS-CIT",
            student_name="Existing",
            father_name="Student",
            surname="One",
            mother_name="Parent",
            date_of_birth=date(2004, 1, 1),
            mobile_own="9988776620",
            parent_mobile="9988776621",
            gender="Male",
            marital_status="Single",
            address="Address",
            city="Pune",
            tehsil_block="Haveli",
            district="Pune",
            pin_code="411001",
            educational_qualification="Graduate",
            theory_batch_time="08:00-09:00",
        )
        candidate = AdmittedStudent.objects.create(
            course="MS-CIT",
            student_name="Candidate",
            father_name="Student",
            surname="Two",
            mother_name="Parent",
            date_of_birth=date(2004, 1, 1),
            mobile_own="9988776622",
            parent_mobile="9988776623",
            gender="Female",
            marital_status="Single",
            address="Address",
            city="Pune",
            tehsil_block="Haveli",
            district="Pune",
            pin_code="411001",
            educational_qualification="Graduate",
        )

        response = self.client.post(
            reverse("update_student_admitted", args=[candidate.id]),
            data='{"theory_batch_time":"08:00-09:00"}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertFalse(payload["success"])
        self.assertIn("full", payload["error"].lower())
        candidate.refresh_from_db()
        self.assertFalse(candidate.theory_batch_time)

    def test_end_batch_page_does_not_preview_already_completed_batch(self):
        admin_group = Group.objects.get(name=ROLE_ADMIN)
        self.user.groups.add(admin_group)
        self.client.force_login(self.user)

        AdmittedStudent.objects.create(
            course="MS-CIT",
            student_name="Completed",
            father_name="Student",
            surname="Batch",
            mother_name="Parent",
            date_of_birth=date(2004, 1, 1),
            mobile_own="9988776630",
            parent_mobile="9988776631",
            gender="Male",
            marital_status="Single",
            address="Address",
            city="Pune",
            tehsil_block="Haveli",
            district="Pune",
            pin_code="411001",
            educational_qualification="Graduate",
            batch_month="April",
            batch_year="2026",
            batch_status="completed",
        )

        response = self.client.get(
            reverse("end_batch"),
            {"batch_month": "April", "batch_year": "2026", "course": "MS-CIT"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No students found for the selected batch.")
        self.assertNotContains(response, "Active Students")

    def test_month_wise_profit_does_not_double_count_custom_course_students(self):
        self.client.force_login(self.user)

        student = AdmittedStudent.objects.create(
            course="Other",
            custom_course="Tally Prime",
            student_name="Custom",
            father_name="Student",
            surname="Profit",
            mother_name="Parent",
            date_of_birth=date(2004, 1, 1),
            mobile_own="9988776640",
            parent_mobile="9988776641",
            gender="Male",
            marital_status="Single",
            address="Address",
            city="Pune",
            tehsil_block="Haveli",
            district="Pune",
            pin_code="411001",
            educational_qualification="Graduate",
            paid_fees="5000.00",
            total_fees="6000.00",
            admission_date=date(2026, 1, 15),
        )
        StudentFinanceDetail.objects.create(
            student=student,
            fees_paid_to_mkcl_1="1000.00",
            fees_paid_to_mkcl_2="500.00",
            fees_paid_to_mkcl_3="0.00",
        )

        response = self.client.get(reverse("month_wise_admission"), {"year": "2026"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["profit_grand_total"], "₹ 3500.00")
        self.assertEqual(len(response.context["monthly_profit_data"]), 1)
        self.assertEqual(response.context["monthly_profit_data"][0]["course"], "Tally Prime")
        self.assertEqual(response.context["monthly_profit_data"][0]["jan"], "₹ 3500.00")

    def test_month_wise_profit_includes_negative_course_totals(self):
        self.client.force_login(self.user)

        student = AdmittedStudent.objects.create(
            course="Marketing 101",
            student_name="Negative",
            father_name="Profit",
            surname="Case",
            mother_name="Parent",
            date_of_birth=date(2004, 1, 1),
            mobile_own="9988776650",
            parent_mobile="9988776651",
            gender="Male",
            marital_status="Single",
            address="Address",
            city="Pune",
            tehsil_block="Haveli",
            district="Pune",
            pin_code="411001",
            educational_qualification="Graduate",
            paid_fees="0.00",
            total_fees="5000.00",
            admission_date=date(2026, 4, 10),
        )
        StudentFinanceDetail.objects.create(
            student=student,
            fees_paid_to_mkcl_1="700.00",
        )

        response = self.client.get(reverse("month_wise_admission"), {"year": "2026"})

        self.assertEqual(response.status_code, 200)
        negative_row = next(
            item for item in response.context["monthly_profit_data"] if item["course"] == "Marketing 101"
        )
        self.assertEqual(negative_row["april"], "₹ -700.00")
        self.assertEqual(negative_row["total"], "₹ -700.00")

    def test_statistics_finance_card_uses_student_finance_profit(self):
        self.client.force_login(self.user)

        student = AdmittedStudent.objects.create(
            course="MS-CIT",
            student_name="Finance",
            father_name="Card",
            surname="Student",
            mother_name="Parent",
            date_of_birth=date(2004, 1, 1),
            mobile_own="9988776620",
            parent_mobile="9988776621",
            gender="Male",
            marital_status="Single",
            address="Address",
            city="Pune",
            tehsil_block="Haveli",
            district="Pune",
            pin_code="411001",
            educational_qualification="Graduate",
            total_fees="6000.00",
            paid_fees="5000.00",
            admission_date=date(2026, 1, 10),
        )
        StudentFinanceDetail.objects.create(
            student=student,
            fees_paid_to_mkcl_1="1000.00",
            fees_paid_to_mkcl_2="500.00",
            fees_paid_to_mkcl_3="250.00",
        )

        response = self.client.get(reverse("statistics"), {"year": "2026"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(response.context["total_profit"]), "3250.00")

    def test_unauthorized_user_cannot_end_batch(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("end_batch"))
        self.assertEqual(response.status_code, 302)

    def test_logout_only_allows_post(self):
        self.client.force_login(self.user)
        # GET request to logout should fail with 405 Method Not Allowed
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 405)
        
        # POST request to logout should succeed and redirect
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("home"))

    def test_batch_capacity_validation_raises_validation_error(self):
        from django.core.exceptions import ValidationError
        
        # Create a batch with capacity 1
        Batch.objects.create(batch_type="Theory", time_slot="08:00-09:00", capacity=1)
        
        # Add first student to the batch
        AdmittedStudent.objects.create(
            course="MS-CIT",
            student_name="Student1",
            father_name="Father1",
            surname="Surname1",
            mother_name="Mother1",
            date_of_birth=date(2004, 1, 1),
            mobile_own="9988776611",
            parent_mobile="9988776612",
            gender="Female",
            marital_status="Single",
            address="Address 1",
            city="Pune",
            tehsil_block="Haveli",
            district="Pune",
            pin_code="411001",
            educational_qualification="HSC",
            theory_batch_time="08:00-09:00",
            total_fees="5000.00",
        )
        
        # Attempt to create second student in same batch
        student2 = AdmittedStudent(
            course="MS-CIT",
            student_name="Student2",
            father_name="Father2",
            surname="Surname2",
            mother_name="Mother2",
            date_of_birth=date(2004, 1, 1),
            mobile_own="9988776622",
            parent_mobile="9988776623",
            gender="Female",
            marital_status="Single",
            address="Address 2",
            city="Pune",
            tehsil_block="Haveli",
            district="Pune",
            pin_code="411001",
            educational_qualification="HSC",
            theory_batch_time="08:00-09:00",
            total_fees="5000.00",
        )
        
        # Should raise ValidationError
        with self.assertRaises(ValidationError) as ctx:
            student2.full_clean()
        
        self.assertIn("theory_batch_time", ctx.exception.message_dict)
        self.assertIn("full", ctx.exception.message_dict["theory_batch_time"][0])

    def test_database_backup_restore_guards_non_sqlite(self):
        self.client.force_login(self.user)
        self.user.is_staff = True
        self.user.save()

        non_sqlite_databases = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "test_db",
            }
        }
        with override_settings(DATABASES=non_sqlite_databases):
            response = self.client.get(reverse("export_database"))
            self.assertEqual(response.status_code, 400)
            payload = response.json()
            self.assertFalse(payload["success"])
            self.assertIn("SQLite", payload["error"])

            response = self.client.post(reverse("import_database"), {"database_file": "dummy"})
            self.assertEqual(response.status_code, 400)
            payload = response.json()
            self.assertFalse(payload["success"])
            self.assertIn("SQLite", payload["error"])

