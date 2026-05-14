from datetime import date
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from core.models import AdmittedStudent, Attendance, AuditLog, DailySalesEntry, DailySalesLine, Enquiry, SalesReceipt, SalesReceiptLine
from core.permissions import ROLE_ADMIN, ROLE_ATTENDANCE_MANAGER, ensure_role_groups
from core.validators import validate_filename, validate_image_file
from inventory.models import Category, Item


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

    def _make_inventory_item(self, **overrides):
        category = Category.objects.create(name="Accessories")
        payload = {
            "name": "USB Keyboard",
            "sku": "ACC-KEY-001",
            "category": category,
            "current_stock": 5,
            "minimum_stock": 1,
            "maximum_stock": 50,
            "average_purchase_rate": Decimal("250.00"),
            "latest_purchase_rate": Decimal("250.00"),
            "selling_price": Decimal("400.00"),
            "gst_percentage": Decimal("18.00"),
        }
        payload.update(overrides)
        return Item.objects.create(**payload)

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

    def test_delete_sales_receipt_restores_inventory_stock(self):
        admin_group = Group.objects.get(name=ROLE_ADMIN)
        self.user.groups.add(admin_group)
        item = self._make_inventory_item(current_stock=3)
        receipt = SalesReceipt.objects.create(
            customer_name="Walk-in Customer",
            sale_date=date(2026, 5, 12),
            payment_mode="Cash",
            subtotal=Decimal("800.00"),
            discount_amount=Decimal("0.00"),
            grand_total=Decimal("800.00"),
            created_by=self.user,
        )
        SalesReceiptLine.objects.create(
            receipt=receipt,
            line_type="item",
            inventory_item=item,
            description=item.name,
            quantity=2,
            unit_price=Decimal("400.00"),
            line_total=Decimal("800.00"),
        )
        item.current_stock = 1
        item.save(update_fields=["current_stock", "updated_at"])

        response = self.client.post(reverse("delete_sales_receipt", args=[receipt.id]), {"next": reverse("sales_receipt_history")})

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("sales_receipt_history"))
        self.assertFalse(SalesReceipt.objects.filter(id=receipt.id).exists())
        item.refresh_from_db()
        self.assertEqual(item.current_stock, 3)
        self.assertTrue(AuditLog.objects.filter(action="sales.receipt_deleted").exists())

    def test_daily_sales_entry_reduces_inventory_and_records_profit(self):
        admin_group = Group.objects.get(name=ROLE_ADMIN)
        self.user.groups.add(admin_group)
        item = self._make_inventory_item(current_stock=5, average_purchase_rate=Decimal("250.00"), selling_price=Decimal("400.00"))

        response = self.client.post(
            reverse("daily_sales_register"),
            {
                "sale_date": "2026-05-12",
                "payment_mode": "Cash",
                "notes": "Counter sales",
                "line_type[]": ["item", "service"],
                "inventory_item_id[]": [str(item.id), ""],
                "description[]": ["", "Laptop cleaning"],
                "quantity[]": ["2", "1"],
                "unit_price[]": ["400.00", "300.00"],
                "unit_cost[]": ["0", "50.00"],
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(DailySalesEntry.objects.count(), 1)
        entry = DailySalesEntry.objects.get()
        self.assertEqual(entry.total_amount, Decimal("1100.00"))
        self.assertEqual(entry.total_cost, Decimal("550.00"))
        self.assertEqual(entry.total_profit, Decimal("550.00"))
        item.refresh_from_db()
        self.assertEqual(item.current_stock, 3)

    def test_daily_sales_same_day_and_payment_mode_updates_existing_record(self):
        admin_group = Group.objects.get(name=ROLE_ADMIN)
        self.user.groups.add(admin_group)
        item = self._make_inventory_item(current_stock=6, average_purchase_rate=Decimal("250.00"), selling_price=Decimal("400.00"))

        first_response = self.client.post(
            reverse("daily_sales_register"),
            {
                "sale_date": "2026-05-12",
                "payment_mode": "Cash",
                "notes": "Morning sales",
                "line_type[]": ["item"],
                "inventory_item_id[]": [str(item.id)],
                "description[]": [""],
                "quantity[]": ["1"],
                "unit_price[]": ["400.00"],
                "unit_cost[]": ["0"],
            },
            follow=True,
        )
        self.assertEqual(first_response.status_code, 200)

        second_response = self.client.post(
            reverse("daily_sales_register"),
            {
                "sale_date": "2026-05-12",
                "payment_mode": "Cash",
                "notes": "Evening sales",
                "line_type[]": ["service"],
                "inventory_item_id[]": [""],
                "description[]": ["Windows install"],
                "quantity[]": ["1"],
                "unit_price[]": ["300.00"],
                "unit_cost[]": ["50.00"],
            },
            follow=True,
        )
        self.assertEqual(second_response.status_code, 200)

        self.assertEqual(DailySalesEntry.objects.count(), 1)
        entry = DailySalesEntry.objects.get()
        self.assertEqual(entry.total_amount, Decimal("700.00"))
        self.assertEqual(entry.total_cost, Decimal("300.00"))
        self.assertEqual(entry.total_profit, Decimal("400.00"))
        self.assertEqual(entry.lines.count(), 2)
        self.assertIn("Morning sales", entry.notes)
        self.assertIn("Evening sales", entry.notes)
        item.refresh_from_db()
        self.assertEqual(item.current_stock, 5)

    def test_daily_sales_entry_can_be_edited(self):
        admin_group = Group.objects.get(name=ROLE_ADMIN)
        self.user.groups.add(admin_group)
        item = self._make_inventory_item(current_stock=8, average_purchase_rate=Decimal("250.00"), selling_price=Decimal("400.00"))

        self.client.post(
            reverse("daily_sales_register"),
            {
                "sale_date": "2026-05-12",
                "payment_mode": "Cash",
                "notes": "Original sale",
                "line_type[]": ["item"],
                "inventory_item_id[]": [str(item.id)],
                "description[]": [""],
                "quantity[]": ["2"],
                "unit_price[]": ["400.00"],
                "unit_cost[]": ["0"],
            },
            follow=True,
        )

        entry = DailySalesEntry.objects.get()
        item.refresh_from_db()
        self.assertEqual(item.current_stock, 6)

        response = self.client.post(
            reverse("daily_sales_register"),
            {
                "entry_id": str(entry.id),
                "sale_date": "2026-05-12",
                "payment_mode": "Cash",
                "notes": "Updated sale",
                "line_type[]": ["item", "service"],
                "inventory_item_id[]": [str(item.id), ""],
                "description[]": ["", "Setup help"],
                "quantity[]": ["1", "1"],
                "unit_price[]": ["400.00", "150.00"],
                "unit_cost[]": ["0", "25.00"],
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        entry.refresh_from_db()
        self.assertEqual(entry.lines.count(), 2)
        self.assertEqual(entry.total_amount, Decimal("550.00"))
        self.assertEqual(entry.total_cost, Decimal("275.00"))
        self.assertEqual(entry.total_profit, Decimal("275.00"))
        self.assertEqual(entry.notes, "Updated sale")
        item.refresh_from_db()
        self.assertEqual(item.current_stock, 7)

    def test_delete_daily_sales_entry_restores_inventory_stock(self):
        admin_group = Group.objects.get(name=ROLE_ADMIN)
        self.user.groups.add(admin_group)
        item = self._make_inventory_item(current_stock=5, average_purchase_rate=Decimal("250.00"), selling_price=Decimal("400.00"))
        entry = DailySalesEntry.objects.create(
            sale_date=date(2026, 5, 12),
            payment_mode="Cash",
            notes="Counter sale",
            total_amount=Decimal("800.00"),
            total_cost=Decimal("500.00"),
            total_profit=Decimal("300.00"),
            created_by=self.user,
        )
        DailySalesLine.objects.create(
            entry=entry,
            line_type="item",
            inventory_item=item,
            description=item.name,
            quantity=2,
            unit_price=Decimal("400.00"),
            unit_cost=Decimal("250.00"),
            line_total=Decimal("800.00"),
            line_profit=Decimal("300.00"),
        )
        item.current_stock = 3
        item.save(update_fields=["current_stock", "updated_at"])

        response = self.client.post(
            reverse("delete_daily_sales_entry", args=[entry.id]),
            {"next": reverse("daily_sales_register")},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(DailySalesEntry.objects.filter(id=entry.id).exists())
        item.refresh_from_db()
        self.assertEqual(item.current_stock, 5)
        self.assertTrue(AuditLog.objects.filter(action="sales.daily_entry_deleted").exists())

    def test_daily_sales_report_shows_historical_day(self):
        admin_group = Group.objects.get(name=ROLE_ADMIN)
        self.user.groups.add(admin_group)
        DailySalesEntry.objects.create(
            sale_date=date(2026, 5, 10),
            payment_mode="Cash",
            total_amount=Decimal("1000.00"),
            total_cost=Decimal("600.00"),
            total_profit=Decimal("400.00"),
            created_by=self.user,
        )

        response = self.client.get(reverse("daily_sales_report"), {"date": "2026-05-10", "from_date": "2026-05-01", "to_date": "2026-05-31"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "10 May 2026")
        self.assertContains(response, "400.00")

    def test_daily_sales_report_syncs_unsynced_sales_receipt_lines(self):
        admin_group = Group.objects.get(name=ROLE_ADMIN)
        self.user.groups.add(admin_group)
        item = self._make_inventory_item(current_stock=5, average_purchase_rate=Decimal("250.00"), selling_price=Decimal("400.00"))
        receipt = SalesReceipt.objects.create(
            customer_name="Walk-in Customer",
            sale_date=date(2026, 5, 10),
            payment_mode="Cash",
            subtotal=Decimal("800.00"),
            discount_amount=Decimal("0.00"),
            grand_total=Decimal("800.00"),
            created_by=self.user,
        )
        SalesReceiptLine.objects.create(
            receipt=receipt,
            line_type="item",
            inventory_item=item,
            description=item.name,
            quantity=2,
            unit_price=Decimal("400.00"),
            line_total=Decimal("800.00"),
        )

        response = self.client.get(
            reverse("daily_sales_report"),
            {"date": "2026-05-10", "from_date": "2026-05-01", "to_date": "2026-05-31"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(DailySalesEntry.objects.count(), 1)
        entry = DailySalesEntry.objects.get()
        self.assertEqual(entry.sale_date, date(2026, 5, 10))
        self.assertEqual(entry.total_amount, Decimal("800.00"))
        self.assertEqual(entry.total_cost, Decimal("500.00"))
        self.assertEqual(entry.total_profit, Decimal("300.00"))
        self.assertTrue(DailySalesLine.objects.filter(entry=entry, sales_receipt=receipt).exists())
        self.assertContains(response, receipt.receipt_no)
        self.assertContains(response, "800.00")

    def test_sales_receipt_creates_daily_sales_record(self):
        admin_group = Group.objects.get(name=ROLE_ADMIN)
        self.user.groups.add(admin_group)
        item = self._make_inventory_item(current_stock=5, average_purchase_rate=Decimal("250.00"), selling_price=Decimal("400.00"))

        response = self.client.post(
            reverse("sales_receipts"),
            {
                "customer_name": "Walk-in Customer",
                "customer_phone": "9876543210",
                "customer_address": "Main Road",
                "sale_date": "2026-05-12",
                "payment_mode": "Cash",
                "notes": "Counter invoice",
                "discount_amount": "0",
                "line_type[]": ["item", "service"],
                "inventory_item_id[]": [str(item.id), ""],
                "description[]": ["", "OS install"],
                "quantity[]": ["2", "1"],
                "unit_price[]": ["400.00", "300.00"],
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(SalesReceipt.objects.count(), 1)
        self.assertEqual(DailySalesEntry.objects.count(), 1)
        daily_entry = DailySalesEntry.objects.get()
        self.assertEqual(daily_entry.total_amount, Decimal("1100.00"))
        self.assertEqual(daily_entry.lines.count(), 2)
        self.assertTrue(DailySalesLine.objects.filter(entry=daily_entry, sales_receipt__isnull=False).exists())
        item.refresh_from_db()
        self.assertEqual(item.current_stock, 3)

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
