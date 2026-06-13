from datetime import date
import sys
from unittest.mock import patch, MagicMock

# Stub twilio module for environments where it is not installed
if "twilio" not in sys.modules:
    mock_twilio = MagicMock()
    sys.modules["twilio"] = mock_twilio
    sys.modules["twilio.rest"] = mock_twilio.rest

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase, override_settings, TransactionTestCase
from django.urls import reverse

from core.services.whatsapp_service import (
    format_whatsapp_number,
    send_whatsapp_message,
    send_admission_notification,
    send_payment_notification,
)

from core.models import (
    AdmittedStudent,
    Attendance,
    AuditLog,
    Batch,
    BatchActionLog,
    FeePayment,
    LoginAttempt,
    StudentFinanceDetail,
    WhatsAppConfig,
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


class WhatsAppNotificationTests(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password123")
        self.whatsapp_config = WhatsAppConfig.get_solo()
        self.whatsapp_config.is_enabled = True
        self.whatsapp_config.provider = "console"
        self.whatsapp_config.save()
        
        self.student = AdmittedStudent.objects.create(
            course="MS-CIT",
            student_name="Rahul",
            father_name="Kumar",
            surname="Sharma",
            date_of_birth="2000-01-01",
            mobile_own="9876543210",
            gender="Male",
            marital_status="Single",
            address="Some Address",
            city="Pune",
            tehsil_block="Pune",
            district="Pune",
            pin_code="411001",
            educational_qualification="Graduate",
            total_fees=5000.00
        )

    def test_format_whatsapp_number(self):
        # 10-digit Indian numbers should get prepended with +91
        self.assertEqual(format_whatsapp_number("9876543210"), "+919876543210")
        # Numbers starting with + should not change
        self.assertEqual(format_whatsapp_number("+14155238886"), "+14155238886")
        # Numbers starting with country code but no + should get +
        self.assertEqual(format_whatsapp_number("919876543210"), "+919876543210")
        # Return empty string for invalid input
        self.assertEqual(format_whatsapp_number(""), "")

    def test_send_whatsapp_message_disabled(self):
        self.whatsapp_config.is_enabled = False
        self.whatsapp_config.save()
        self.assertFalse(send_whatsapp_message("9876543210", "Hello Test"))

    def test_send_whatsapp_message_console(self):
        self.whatsapp_config.is_enabled = True
        self.whatsapp_config.provider = "console"
        self.whatsapp_config.save()
        self.assertTrue(send_whatsapp_message("9876543210", "Hello Test"))

    @patch("core.services.whatsapp_service.logger")
    @patch("twilio.rest.Client")
    def test_send_whatsapp_message_twilio(self, mock_client_class, mock_logger):
        self.whatsapp_config.is_enabled = True
        self.whatsapp_config.provider = "twilio"
        self.whatsapp_config.twilio_sid = "ACxxxx"
        self.whatsapp_config.twilio_auth_token = "auth_token"
        self.whatsapp_config.twilio_from = "whatsapp:+14155238886"
        self.whatsapp_config.save()

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_message = MagicMock()
        mock_message.sid = "SMxxxx"
        mock_client.messages.create.return_value = mock_message

        res = send_whatsapp_message("9876543210", "Hello Twilio")
        self.assertTrue(res)
        mock_client.messages.create.assert_called_once_with(
            body="Hello Twilio",
            from_="whatsapp:+14155238886",
            to="whatsapp:+919876543210"
        )

    @patch("urllib.request.urlopen")
    def test_send_whatsapp_message_meta(self, mock_urlopen):
        self.whatsapp_config.is_enabled = True
        self.whatsapp_config.provider = "meta"
        self.whatsapp_config.meta_token = "meta_token"
        self.whatsapp_config.meta_phone_id = "phone_id"
        self.whatsapp_config.save()

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"success": true}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = send_whatsapp_message("9876543210", "Hello Meta")
        self.assertTrue(res)

        args, kwargs = mock_urlopen.call_args
        req = args[0]
        self.assertEqual(req.get_full_url(), "https://graph.facebook.com/v18.0/phone_id/messages")
        self.assertEqual(req.get_header("Authorization"), "Bearer meta_token")
        self.assertEqual(req.get_header("Content-type"), "application/json")

    @patch("urllib.request.urlopen")
    def test_send_whatsapp_message_custom(self, mock_urlopen):
        self.whatsapp_config.is_enabled = True
        self.whatsapp_config.provider = "custom"
        self.whatsapp_config.custom_url = "https://api.ultramsg.com/instance123/messages/chat"
        self.whatsapp_config.custom_token = "custom_token"
        self.whatsapp_config.save()

        mock_response = MagicMock()
        mock_response.read.return_value = b"success"
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = send_whatsapp_message("9876543210", "Hello Custom")
        self.assertTrue(res)

        args, kwargs = mock_urlopen.call_args
        req = args[0]
        self.assertEqual(req.get_full_url(), "https://api.ultramsg.com/instance123/messages/chat")
        self.assertEqual(req.get_header("Authorization"), "Bearer custom_token")

    @override_settings(WHATSAPP_ENABLED=True, WHATSAPP_PROVIDER="console")
    @patch("core.services.whatsapp_service.send_whatsapp_message")
    def test_send_admission_notification(self, mock_send_message):
        send_admission_notification(self.student)
        mock_send_message.assert_called_once()
        args, kwargs = mock_send_message.call_args
        self.assertEqual(args[0], "9876543210")
        self.assertIn("Sharma Rahul Kumar", args[1])
        self.assertIn("MS-CIT", args[1])

    @override_settings(WHATSAPP_ENABLED=True, WHATSAPP_PROVIDER="console")
    @patch("core.services.whatsapp_service.send_whatsapp_message")
    def test_send_payment_notification(self, mock_send_message):
        payment = FeePayment.objects.create(
            student=self.student,
            amount=1000.00,
            payment_mode="Cash",
            payment_date="2026-06-09",
            remarks="Payment 1",
            total_fees_at_payment=5000.00,
            paid_before_this=0.00,
            remaining_after_this=4000.00
        )
        send_payment_notification(payment)
        mock_send_message.assert_called_once()
        args, kwargs = mock_send_message.call_args
        self.assertEqual(args[0], "9876543210")
        self.assertIn("Sharma Rahul Kumar", args[1])
        self.assertIn("1000", args[1])
        self.assertIn("4000", args[1])

    @override_settings(WHATSAPP_ENABLED=True, WHATSAPP_PROVIDER="console")
    @patch("core.services.whatsapp_service.send_admission_notification")
    def test_create_admission_triggers_whatsapp(self, mock_send_adm):
        from core.forms import AdmittedStudentForm
        from core.services.admission_service import create_admission
        form_data = {
            "course": "MS-CIT",
            "student_name": "Ajit",
            "father_name": "Sunil",
            "surname": "Jadhav",
            "date_of_birth": "2002-05-20",
            "mobile_own": "9876540000",
            "gender": "Male",
            "marital_status": "Single",
            "address": "Address",
            "city": "Pune",
            "tehsil_block": "Haveli",
            "district": "Pune",
            "pin_code": "411001",
            "educational_qualification": "Graduate",
            "total_fees": "5000.00"
        }
        form = AdmittedStudentForm(data=form_data)
        self.assertTrue(form.is_valid())

        create_admission(form=form, actor=self.user)
        mock_send_adm.assert_called_once()

    @override_settings(WHATSAPP_ENABLED=True, WHATSAPP_PROVIDER="console")
    @patch("core.services.whatsapp_service.send_payment_notification")
    def test_record_fee_payment_triggers_whatsapp(self, mock_send_payment):
        from core.services.fee_service import record_fee_payment
        record_fee_payment(
            student_id=self.student.id,
            amount="1000.00",
            payment_mode="Cash",
            payment_date="2026-06-09",
            remarks="Payment 1"
        )
        mock_send_payment.assert_called_once()

    def test_whatsapp_settings_view_unauthenticated(self):
        response = self.client.get(reverse("whatsapp_settings"))
        self.assertEqual(response.status_code, 302)

    def test_whatsapp_settings_view_non_staff_denied(self):
        non_staff = User.objects.create_user(username="studentuser", password="password123")
        self.client.force_login(non_staff)
        response = self.client.get(reverse("whatsapp_settings"))
        self.assertEqual(response.status_code, 403)

    def test_whatsapp_settings_view_staff_allowed(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_login(self.user)
        response = self.client.get(reverse("whatsapp_settings"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "WhatsApp Bot Settings")

    def test_whatsapp_settings_view_post_saves(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("whatsapp_settings"),
            {
                "is_enabled": "on",
                "provider": "meta",
                "meta_token": "new_meta_token",
                "meta_phone_id": "new_phone_id",
                "twilio_from": "whatsapp:+14155238886",
                "admission_template": "Hello {student_name}!",
                "payment_template": "Receipt {receipt_no}.",
                "enquiry_template": "Enquiry {student_name}.",
                "absent_template": "Absent {student_name}."
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)

        from core.models import WhatsAppConfig
        config = WhatsAppConfig.get_solo()
        self.assertTrue(config.is_enabled)
        self.assertEqual(config.provider, "meta")
        self.assertEqual(config.meta_token, "new_meta_token")
        self.assertEqual(config.meta_phone_id, "new_phone_id")
        self.assertEqual(config.admission_template, "Hello {student_name}!")

    @override_settings(WHATSAPP_ENABLED=True, WHATSAPP_PROVIDER="console")
    @patch("core.services.whatsapp_service.send_whatsapp_message")
    def test_send_enquiry_notification(self, mock_send_message):
        from core.models import Enquiry
        from core.services.whatsapp_service import send_enquiry_notification
        enquiry = Enquiry.objects.create(
            name="Amit",
            mobile="9876543211",
            course="MS-CIT"
        )
        send_enquiry_notification(enquiry)
        mock_send_message.assert_called_once()
        args, kwargs = mock_send_message.call_args
        self.assertEqual(args[0], "9876543211")
        self.assertIn("Amit", args[1])

    @override_settings(WHATSAPP_ENABLED=True, WHATSAPP_PROVIDER="console")
    @patch("core.services.whatsapp_service.send_whatsapp_message")
    def test_send_absent_notification(self, mock_send_message):
        from core.services.whatsapp_service import send_absent_notification
        send_absent_notification(self.student, date(2026, 6, 11), "10:00 AM", "theory")
        mock_send_message.assert_called_once()
        args, kwargs = mock_send_message.call_args
        self.assertEqual(args[0], "9876543210")
        self.assertIn("Sharma Rahul Kumar", args[1])
        self.assertIn("11-06-2026", args[1])


class StudentExamRecordTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import Group
        from decimal import Decimal
        ensure_role_groups()
        self.client = Client()
        self.admin_user = User.objects.create_superuser(username="adminuser", password="password123")
        self.counselor_user = User.objects.create_user(username="counseloruser", password="password123")
        
        counselor_group, _ = Group.objects.get_or_create(name="Counselor")
        self.counselor_user.groups.add(counselor_group)
        
        self.student = AdmittedStudent.objects.create(
            course="MS-CIT",
            student_name="Rahul",
            father_name="Kumar",
            surname="Sharma",
            date_of_birth="2000-01-01",
            mobile_own="9876543210",
            gender="Male",
            marital_status="Single",
            address="Pune",
            city="Pune",
            tehsil_block="Pune",
            district="Pune",
            pin_code="411001",
            educational_qualification="Graduate",
            total_fees=5000.00,
            student_id="STU12345"
        )

    def test_exam_record_crud(self):
        from core.models import StudentExamRecord
        from decimal import Decimal
        self.client.force_login(self.admin_user)
        
        # Add
        response = self.client.post(
            reverse("add_exam_record"),
            {
                "student": self.student.id,
                "student_name": "Rahul Sharma",
                "learner_id": "STU12345",
                "exam_date": "2026-06-11",
                "course": "MS-CIT",
                "course_batch": "June 2026",
                "result": "Pass",
                "percentage": "85.50"
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(StudentExamRecord.objects.filter(student_name="Rahul Sharma").exists())
        record = StudentExamRecord.objects.get(student_name="Rahul Sharma")
        
        # Edit
        response = self.client.post(
            reverse("edit_exam_record", args=[record.id]),
            {
                "student": self.student.id,
                "student_name": "Rahul Sharma Edited",
                "learner_id": "STU12345",
                "exam_date": "2026-06-11",
                "course": "MS-CIT",
                "course_batch": "June 2026",
                "result": "Pass",
                "percentage": "90.00"
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        record.refresh_from_db()
        self.assertEqual(record.student_name, "Rahul Sharma Edited")
        self.assertEqual(record.percentage, Decimal("90.00"))
        
        # Delete
        response = self.client.post(
            reverse("delete_exam_record", args=[record.id]),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(StudentExamRecord.objects.filter(id=record.id).exists())

    def test_parse_excel_date(self):
        from core.views import parse_excel_date
        from datetime import datetime
        dt_val = datetime(2026, 6, 11)
        self.assertEqual(parse_excel_date(dt_val), date(2026, 6, 11))
        self.assertEqual(parse_excel_date("2026-06-11"), date(2026, 6, 11))
        self.assertEqual(parse_excel_date("11-06-2026"), date(2026, 6, 11))
        self.assertEqual(parse_excel_date("11/06/2026"), date(2026, 6, 11))
        self.assertEqual(parse_excel_date(46182), date(2026, 6, 9))

    def test_import_exam_records_excel(self):
        from core.models import StudentExamRecord
        import openpyxl
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Learner ID", "Student Name", "Exam Date", "Course", "Course Batch", "Result", "Percentage"])
        ws.append(["STU12345", "Rahul Sharma", "2026-06-11", "MS-CIT", "June 2026", "Pass", "85.50"])
        ws.append(["", "Walkin Student", "2026-06-12", "Tally", "June 2026", "Fail", "35.00"])

        f = BytesIO()
        wb.save(f)
        f.seek(0)
        excel_file = SimpleUploadedFile("exams.xlsx", f.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        self.client.force_login(self.counselor_user)
        response = self.client.post(
            reverse("import_exam_records"),
            {"excel_file": excel_file},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(StudentExamRecord.objects.count(), 2)
        
        rec1 = StudentExamRecord.objects.get(student_name="Rahul Sharma")
        self.assertEqual(rec1.student, self.student)
        self.assertEqual(rec1.result, "Pass")
        
        rec2 = StudentExamRecord.objects.get(student_name="Walkin Student")
        self.assertIsNone(rec2.student)
        self.assertEqual(rec2.result, "Fail")



