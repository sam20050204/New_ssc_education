from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from inventory.models import Item as InventoryItem

from core.audit_logs import log_audit_event
from core.models import DailySalesEntry, DailySalesLine, SalesReceipt
from core.utils import number_to_words


class SalesService:
    @staticmethod
    def receipt_queryset(include_deleted=False):
        queryset = SalesReceipt.objects.select_related(
            "created_by",
            "modified_by",
            "deleted_by",
        ).prefetch_related("lines__inventory_item", "lines__sales_item")
        if not include_deleted:
            queryset = queryset.filter(is_deleted=False)
        return queryset

    @classmethod
    def all_receipts_including_deleted(cls):
        return cls.receipt_queryset(include_deleted=True)

    @classmethod
    def get_receipt(cls, receipt_id, include_deleted=False):
        if not receipt_id:
            return None
        try:
            return cls.receipt_queryset(include_deleted=include_deleted).get(id=int(receipt_id))
        except (SalesReceipt.DoesNotExist, TypeError, ValueError):
            return None

    @staticmethod
    def daily_entry_queryset(include_deleted=False):
        queryset = DailySalesEntry.objects.select_related(
            "created_by",
            "modified_by",
            "deleted_by",
        ).prefetch_related("lines__inventory_item", "lines__sales_receipt")
        if not include_deleted:
            queryset = queryset.filter(is_deleted=False)
        return queryset

    @classmethod
    def get_daily_entry(cls, entry_id, include_deleted=False):
        if not entry_id:
            return None
        try:
            return cls.daily_entry_queryset(include_deleted=include_deleted).get(id=int(entry_id))
        except (DailySalesEntry.DoesNotExist, TypeError, ValueError):
            return None

    @staticmethod
    def recalculate_entry(entry):
        totals = entry.lines.aggregate(
            total_amount=Sum("line_total"),
            total_profit=Sum("line_profit"),
        )
        total_amount = totals["total_amount"] or Decimal("0")
        total_profit = totals["total_profit"] or Decimal("0")
        entry.total_amount = total_amount
        entry.total_profit = total_profit
        entry.total_cost = total_amount - total_profit
        entry.save(update_fields=["total_amount", "total_cost", "total_profit", "updated_at"])
        return entry

    @classmethod
    def get_or_create_entry(cls, *, sale_date, payment_mode, notes="", created_by=None):
        entry = (
            DailySalesEntry.objects.select_for_update()
            .filter(sale_date=sale_date, payment_mode=payment_mode, is_deleted=False)
            .order_by("created_at", "id")
            .first()
        )
        created_new_entry = entry is None

        if entry is None:
            entry = DailySalesEntry.objects.create(
                sale_date=sale_date,
                payment_mode=payment_mode,
                notes=notes,
                total_amount=Decimal("0"),
                total_cost=Decimal("0"),
                total_profit=Decimal("0"),
                created_by=created_by,
            )
        elif notes:
            existing_notes = (entry.notes or "").strip()
            if existing_notes:
                if notes not in existing_notes:
                    entry.notes = f"{existing_notes}\n{notes}"
                    entry.save(update_fields=["notes", "updated_at"])
            else:
                entry.notes = notes
                entry.save(update_fields=["notes", "updated_at"])

        return entry, created_new_entry

    @classmethod
    def sync_receipt_to_daily(cls, receipt, *, actor=None, request=None):
        existing_entries = list(
            DailySalesEntry.objects.filter(lines__sales_receipt=receipt, is_deleted=False).distinct()
        )
        if existing_entries:
            DailySalesLine.objects.filter(sales_receipt=receipt).delete()
            for existing_entry in existing_entries:
                cls.recalculate_entry(existing_entry)

        entry, created_new_entry = cls.get_or_create_entry(
            sale_date=receipt.sale_date,
            payment_mode=receipt.payment_mode,
            notes=f"Sales receipt {receipt.receipt_no}",
            created_by=receipt.created_by,
        )

        for line in receipt.lines.all():
            cost_price = line.cost_price or Decimal("0")
            if cost_price == Decimal("0"):
                if line.inventory_item_id and line.inventory_item:
                    cost_price = line.inventory_item.average_purchase_rate or Decimal("0")
                elif line.sales_item_id and line.sales_item:
                    cost_price = line.sales_item.purchase_rate or Decimal("0")
            line_cost = cost_price * line.quantity
            DailySalesLine.objects.create(
                entry=entry,
                sales_receipt=receipt,
                line_type=line.line_type,
                inventory_item=line.inventory_item,
                description=line.description,
                quantity=line.quantity,
                unit_price=line.unit_price,
                unit_cost=cost_price,
                cost_price=cost_price,
                line_total=line.line_total,
                line_profit=line.line_total - line_cost,
            )

        if receipt.discount_amount and receipt.discount_amount > Decimal("0"):
            DailySalesLine.objects.create(
                entry=entry,
                sales_receipt=receipt,
                line_type="service",
                inventory_item=None,
                description=f"Discount on {receipt.receipt_no}",
                quantity=1,
                unit_price=Decimal("0"),
                unit_cost=Decimal("0"),
                cost_price=Decimal("0"),
                line_total=-receipt.discount_amount,
                line_profit=-receipt.discount_amount,
            )

        cls.recalculate_entry(entry)

        if actor and request:
            action = "sales.daily_entry_created" if created_new_entry else "sales.daily_entry_updated"
            log_audit_event(
                action=action,
                actor=actor,
                target=entry,
                request=request,
                metadata={
                    "entry_date": entry.sale_date.isoformat(),
                    "total_amount": str(entry.total_amount),
                    "line_count": entry.lines.count(),
                    "payment_mode": entry.payment_mode,
                },
            )

        return entry

    @classmethod
    def ensure_synced(cls, *, from_date, to_date, actor=None, request=None):
        receipts = (
            SalesReceipt.objects.filter(sale_date__gte=from_date, sale_date__lte=to_date, is_deleted=False)
            .prefetch_related("lines__inventory_item", "lines__sales_item", "daily_sales_lines")
            .order_by("sale_date", "created_at", "id")
        )
        for receipt in receipts:
            if receipt.daily_sales_lines.exists():
                continue
            cls.sync_receipt_to_daily(receipt, actor=actor, request=request)

    @staticmethod
    def restore_inventory(entry):
        inventory_adjustments = {}
        for line in entry.lines.filter(sales_receipt__isnull=True, line_type="item", inventory_item__isnull=False):
            inventory_adjustments[line.inventory_item_id] = inventory_adjustments.get(line.inventory_item_id, 0) + line.quantity

        if not inventory_adjustments:
            return

        items_by_id = {
            item.id: item for item in InventoryItem.objects.select_for_update().filter(id__in=inventory_adjustments.keys())
        }
        for item_id, quantity in inventory_adjustments.items():
            item = items_by_id.get(item_id)
            if item is None:
                continue
            item.current_stock += quantity
            item.save(update_fields=["current_stock", "updated_at"])

    @classmethod
    def build_form_lines(cls, source_entry=None):
        if source_entry is None:
            return [
                {
                    "line_type": "item",
                    "inventory_item_id": "",
                    "description": "",
                    "quantity": 1,
                    "unit_price": Decimal("0"),
                    "unit_cost": Decimal("0"),
                }
            ]

        lines = []
        for line in source_entry.lines.filter(sales_receipt__isnull=True).order_by("id"):
            lines.append(
                {
                    "line_type": line.line_type,
                    "inventory_item_id": str(line.inventory_item_id or ""),
                    "description": line.description,
                    "quantity": line.quantity,
                    "unit_price": line.unit_price,
                    "unit_cost": line.unit_cost,
                }
            )
        return lines or cls.build_form_lines()

    @staticmethod
    def profit_summary(reference_date=None):
        today = reference_date or timezone.localdate()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        year_start = today.replace(month=1, day=1)

        entries = DailySalesEntry.objects.filter(is_deleted=False)
        return {
            "daily_profit": entries.filter(sale_date=today).aggregate(total=Sum("total_profit"))["total"] or Decimal("0"),
            "weekly_profit": entries.filter(sale_date__gte=week_start, sale_date__lte=today).aggregate(total=Sum("total_profit"))["total"] or Decimal("0"),
            "monthly_profit": entries.filter(sale_date__gte=month_start, sale_date__lte=today).aggregate(total=Sum("total_profit"))["total"] or Decimal("0"),
            "yearly_profit": entries.filter(sale_date__gte=year_start, sale_date__lte=today).aggregate(total=Sum("total_profit"))["total"] or Decimal("0"),
        }

    @staticmethod
    def amount_in_words(receipt):
        if not receipt:
            return ""
        try:
            return number_to_words(float(receipt.grand_total or 0))
        except (TypeError, ValueError):
            return ""
