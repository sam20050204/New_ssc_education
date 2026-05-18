from datetime import date
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.db import IntegrityError
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from core.models import DailySalesEntry, DailySalesLine, SalesReceipt, SalesReceiptLine
from core.permissions import ROLE_ADMIN, ensure_role_groups
from core.services.sales_service import SalesService
from inventory.models import Category, Item


@override_settings(ROOT_URLCONF="Project.urls")
class SalesWorkflowTests(TestCase):
    def setUp(self):
        ensure_role_groups()
        self.client = Client()
        self.user = User.objects.create_user(username="sales-admin", password="StrongPass123")
        self.user.groups.add(Group.objects.get(name=ROLE_ADMIN))
        self.client.force_login(self.user)
        self.category_counter = 0

    def _make_item(self, **overrides):
        self.category_counter += 1
        category = Category.objects.create(name=f"Sales Category {self.category_counter}")
        payload = {
            "name": f"Sales Item {self.category_counter}",
            "sku": f"SKU-{self.category_counter:03d}",
            "category": category,
            "current_stock": 10,
            "minimum_stock": 1,
            "maximum_stock": 100,
            "average_purchase_rate": Decimal("50.00"),
            "latest_purchase_rate": Decimal("50.00"),
            "selling_price": Decimal("100.00"),
            "gst_percentage": Decimal("18.00"),
            "is_active": True,
        }
        payload.update(overrides)
        return Item.objects.create(**payload)

    def _receipt_payload(self, item, *, idempotency_key="idem-1", quantity="3", unit_price="100.00"):
        return {
            "customer_name": "Walk-in Customer",
            "customer_phone": "9999999999",
            "customer_address": "Main Road",
            "sale_date": "2026-05-12",
            "payment_mode": "Cash",
            "notes": "Counter sale",
            "discount_amount": "0",
            "idempotency_key": idempotency_key,
            "line_type[]": ["item"],
            "inventory_item_id[]": [str(item.id)],
            "description[]": [item.name],
            "quantity[]": [quantity],
            "unit_price[]": [unit_price],
        }

    def test_receipt_creation_deducts_inventory_stock(self):
        item = self._make_item(current_stock=10)

        response = self.client.post(reverse("sales_receipts"), self._receipt_payload(item), follow=True)

        self.assertEqual(response.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.current_stock, 7)

    def test_receipt_creation_frozen_cost_price(self):
        item = self._make_item(average_purchase_rate=Decimal("50.00"))
        receipt = SalesReceipt.objects.create(
            customer_name="Walk-in Customer",
            sale_date=date(2026, 5, 12),
            payment_mode="Cash",
            subtotal=Decimal("300.00"),
            discount_amount=Decimal("0.00"),
            grand_total=Decimal("300.00"),
            created_by=self.user,
        )
        line = SalesReceiptLine.objects.create(
            receipt=receipt,
            line_type="item",
            inventory_item=item,
            description=item.name,
            quantity=3,
            unit_price=Decimal("100.00"),
            cost_price=Decimal("50.00"),
            line_total=Decimal("300.00"),
        )

        item.average_purchase_rate = Decimal("80.00")
        item.save(update_fields=["average_purchase_rate"])

        line.refresh_from_db()
        self.assertEqual(line.cost_price, Decimal("50.00"))

    def test_duplicate_idempotency_key_blocked(self):
        item = self._make_item()
        payload = self._receipt_payload(item, idempotency_key="dup-key")

        self.client.post(reverse("sales_receipts"), payload, follow=True)
        response = self.client.post(reverse("sales_receipts"), payload, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(SalesReceipt.objects.count(), 1)

    def test_daily_entry_unique_per_date_payment_mode(self):
        DailySalesEntry.objects.create(
            sale_date=date(2026, 5, 12),
            payment_mode="Cash",
            total_amount=Decimal("100.00"),
            total_cost=Decimal("40.00"),
            total_profit=Decimal("60.00"),
            created_by=self.user,
        )

        with self.assertRaises(IntegrityError):
            DailySalesEntry.objects.create(
                sale_date=date(2026, 5, 12),
                payment_mode="Cash",
                total_amount=Decimal("150.00"),
                total_cost=Decimal("50.00"),
                total_profit=Decimal("100.00"),
                created_by=self.user,
            )

    def test_receipt_sync_creates_daily_entry(self):
        item = self._make_item()
        receipt = SalesReceipt.objects.create(
            customer_name="Walk-in Customer",
            sale_date=date(2026, 5, 12),
            payment_mode="Cash",
            subtotal=Decimal("500.00"),
            discount_amount=Decimal("0.00"),
            grand_total=Decimal("500.00"),
            created_by=self.user,
        )
        SalesReceiptLine.objects.create(
            receipt=receipt,
            line_type="item",
            inventory_item=item,
            description=item.name,
            quantity=2,
            unit_price=Decimal("100.00"),
            cost_price=Decimal("50.00"),
            line_total=Decimal("200.00"),
        )
        SalesReceiptLine.objects.create(
            receipt=receipt,
            line_type="service",
            description="Setup",
            quantity=1,
            unit_price=Decimal("300.00"),
            cost_price=Decimal("0.00"),
            line_total=Decimal("300.00"),
        )

        SalesService.sync_receipt_to_daily(receipt)

        entry = DailySalesEntry.objects.get(sale_date=receipt.sale_date, payment_mode=receipt.payment_mode)
        self.assertEqual(entry.lines.count(), 2)

    def test_receipt_with_discount_syncs_correctly(self):
        item = self._make_item()
        receipt = SalesReceipt.objects.create(
            customer_name="Walk-in Customer",
            sale_date=date(2026, 5, 12),
            payment_mode="Cash",
            subtotal=Decimal("1000.00"),
            discount_amount=Decimal("100.00"),
            grand_total=Decimal("900.00"),
            created_by=self.user,
        )
        SalesReceiptLine.objects.create(
            receipt=receipt,
            line_type="item",
            inventory_item=item,
            description=item.name,
            quantity=10,
            unit_price=Decimal("100.00"),
            cost_price=Decimal("50.00"),
            line_total=Decimal("1000.00"),
        )

        entry = SalesService.sync_receipt_to_daily(receipt)

        self.assertEqual(entry.total_amount, Decimal("900.00"))

    def test_recalculate_daily_entry_profit(self):
        entry = DailySalesEntry.objects.create(
            sale_date=date(2026, 5, 12),
            payment_mode="Cash",
            total_amount=Decimal("0.00"),
            total_cost=Decimal("0.00"),
            total_profit=Decimal("0.00"),
            created_by=self.user,
        )
        DailySalesLine.objects.create(
            entry=entry,
            line_type="service",
            description="Repair",
            quantity=1,
            unit_price=Decimal("300.00"),
            unit_cost=Decimal("100.00"),
            cost_price=Decimal("100.00"),
            line_total=Decimal("300.00"),
            line_profit=Decimal("200.00"),
        )
        DailySalesLine.objects.create(
            entry=entry,
            line_type="service",
            description="Install",
            quantity=1,
            unit_price=Decimal("400.00"),
            unit_cost=Decimal("100.00"),
            cost_price=Decimal("100.00"),
            line_total=Decimal("400.00"),
            line_profit=Decimal("300.00"),
        )

        SalesService.recalculate_entry(entry)
        entry.refresh_from_db()

        self.assertEqual(entry.total_profit, Decimal("500.00"))

    def test_soft_delete_receipt_not_in_queryset(self):
        receipt = SalesReceipt.objects.create(
            customer_name="Walk-in Customer",
            sale_date=date(2026, 5, 12),
            payment_mode="Cash",
            subtotal=Decimal("100.00"),
            discount_amount=Decimal("0.00"),
            grand_total=Decimal("100.00"),
            created_by=self.user,
            is_deleted=True,
        )

        self.assertFalse(SalesService.receipt_queryset().filter(id=receipt.id).exists())

    def test_delete_receipt_restores_stock(self):
        item = self._make_item(current_stock=10)
        response = self.client.post(reverse("sales_receipts"), self._receipt_payload(item), follow=True)
        self.assertEqual(response.status_code, 200)
        receipt = SalesReceipt.objects.get()

        delete_response = self.client.post(
            reverse("delete_sales_receipt", args=[receipt.id]),
            {"next": reverse("sales_receipt_history")},
            follow=True,
        )

        self.assertEqual(delete_response.status_code, 200)
        receipt.refresh_from_db()
        item.refresh_from_db()
        self.assertTrue(receipt.is_deleted)
        self.assertEqual(item.current_stock, 10)

    def test_dashboard_total_cost_annotation(self):
        item_a = self._make_item(name="Item A", sku="SKU-A", average_purchase_rate=Decimal("10.00"))
        item_b = self._make_item(name="Item B", sku="SKU-B", average_purchase_rate=Decimal("20.00"))
        item_c = self._make_item(name="Item C", sku="SKU-C", average_purchase_rate=Decimal("5.00"))

        for idx, (item, qty, price, cost) in enumerate(
            [
                (item_a, 2, Decimal("30.00"), Decimal("10.00")),
                (item_b, 1, Decimal("50.00"), Decimal("20.00")),
                (item_c, 4, Decimal("15.00"), Decimal("5.00")),
            ],
            start=1,
        ):
            receipt = SalesReceipt.objects.create(
                customer_name=f"Customer {idx}",
                sale_date=date(2026, 5, 12),
                payment_mode="Cash",
                subtotal=price * qty,
                discount_amount=Decimal("0.00"),
                grand_total=price * qty,
                created_by=self.user,
            )
            SalesReceiptLine.objects.create(
                receipt=receipt,
                line_type="item",
                inventory_item=item,
                description=item.name,
                quantity=qty,
                unit_price=price,
                cost_price=cost,
                line_total=price * qty,
            )

        response = self.client.get(reverse("sales_services_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_profit"], Decimal("110.00"))
