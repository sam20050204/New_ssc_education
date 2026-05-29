"""
Service-layer business logic for inventory workflows.
"""

from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Max, Sum

from inventory.models import (
    Category,
    Inventory,
    Item,
    Purchase,
    SaleReceipt,
    SaleReceiptLine,
    StockMovement,
    Supplier,
)


def get_or_create_category_by_name(name, *, description="", icon=""):
    """Resolve a category by case-insensitive name or create a new active one."""
    normalized_name = (name or "").strip()
    if not normalized_name:
        return None

    category = Category.objects.filter(name__iexact=normalized_name).first()
    if category:
        if not category.is_active:
            category.is_active = True
            category.save(update_fields=["is_active", "updated_at"])
        return category

    category = Category(name=normalized_name, description=description, icon=icon)
    category.save()
    return category


def get_or_create_supplier_by_name(name, **defaults):
    """Resolve a supplier by case-insensitive name or create a new active one."""
    normalized_name = (name or "").strip()
    if not normalized_name:
        return None

    supplier = Supplier.objects.filter(name__iexact=normalized_name).first()
    if supplier:
        if not supplier.is_active:
            supplier.is_active = True
            supplier.save(update_fields=["is_active", "updated_at"])
        return supplier, False

    supplier = Supplier(name=normalized_name, **defaults)
    supplier.save()
    return supplier, True


def record_stock_movement(
    *,
    item,
    movement_type,
    quantity,
    user=None,
    reference="",
    notes="",
):
    """Persist a stock movement entry for auditability."""
    return StockMovement.objects.create(
        item=item,
        movement_type=movement_type,
        quantity=quantity,
        created_by=user,
        reference=reference or None,
        notes=notes or None,
    )


@transaction.atomic
def create_inventory_entry(form, user):
    """Create or update the item snapshot and record its purchase in one transaction."""
    data = form.cleaned_data
    item = data.get("resolved_item")

    if item is None:
        item = Item()

    item.name = data["item_name"].strip()
    if data.get("category"):
        item.category = data["category"]
    item.minimum_stock = data["minimum_stock"]
    item.maximum_stock = data["maximum_stock"]
    item.selling_price = data["selling_price"]
    item.gst_percentage = data["gst_percentage"]
    item.is_active = True

    item.save()

    purchase = Purchase.objects.create(
        item=item,
        supplier=data.get("supplier"),
        purchase_date=data["purchase_date"],
        quantity=data["quantity"],
        purchase_rate=data["purchase_rate"],
        selling_price=data["selling_price"],
        created_by=user,
    )

    Inventory.objects.get_or_create(item=item)
    item.refresh_purchase_metrics()

    record_stock_movement(
        item=item,
        movement_type="purchase",
        quantity=purchase.quantity,
        user=user,
        reference=str(purchase.pk),
        notes=f"Purchase recorded at {purchase.purchase_rate} per unit.",
    )

    return item, purchase


def build_item_insight_payload(item):
    """Return analytics payload used by the unified inventory entry screen."""
    purchases = item.purchases.select_related("supplier").order_by(
        "-purchase_date", "-created_at"
    )
    recent_purchases = list(purchases[:8])
    supplier_history = (
        purchases.values("supplier__id", "supplier__name")
        .annotate(
            purchase_count=Count("id"),
            total_quantity=Sum("quantity"),
            total_spent=Sum("total_purchase_price"),
            latest_purchase_date=Max("purchase_date"),
        )
        .order_by("-latest_purchase_date")
    )

    return {
        "id": item.id,
        "name": item.name,
        "sku": item.sku,
        "category_id": item.category_id,
        "category_name": item.category.name,
        "description": item.description or "",
        "specifications": item.specifications or "",
        "current_stock": item.current_stock,
        "minimum_stock": item.minimum_stock,
        "maximum_stock": item.maximum_stock,
        "average_purchase_rate": float(item.average_purchase_rate or Decimal("0.00")),
        "latest_purchase_rate": float(item.latest_purchase_rate or Decimal("0.00")),
        "selling_price": float(item.selling_price or Decimal("0.00")),
        "gst_percentage": float(item.gst_percentage or Decimal("0.00")),
        "profit_per_unit": float(item.profit_per_unit or Decimal("0.00")),
        "profit_margin_percentage": float(
            item.profit_margin_percentage or Decimal("0.00")
        ),
        "recent_purchases": [
            {
                "purchase_date": purchase.purchase_date.isoformat(),
                "supplier_name": purchase.supplier.name if purchase.supplier else "Walk-in / Unknown",
                "purchase_rate": float(purchase.purchase_rate),
                "selling_price": float(purchase.selling_price or Decimal("0.00")),
                "quantity": purchase.quantity,
                "stock_after_purchase": item.current_stock,
                "invoice_number": purchase.invoice_number or "",
            }
            for purchase in recent_purchases
        ],
        "supplier_history": [
            {
                "supplier_id": row["supplier__id"],
                "supplier_name": row["supplier__name"] or "Walk-in / Unknown",
                "purchase_count": row["purchase_count"] or 0,
                "total_quantity": row["total_quantity"] or 0,
                "total_spent": float(row["total_spent"] or Decimal("0.00")),
                "latest_purchase_date": (
                    row["latest_purchase_date"].isoformat()
                    if row["latest_purchase_date"]
                    else None
                ),
            }
            for row in supplier_history
        ],
    }


@transaction.atomic
def create_sales_receipt(receipt_form, line_formset, user):
    """Create a customer sale receipt, reduce stock, and log stock movements."""
    receipt = receipt_form.save(commit=False)
    receipt.created_by = user
    receipt.save()

    lines = line_formset.save(commit=False)
    active_lines = []
    for line in lines:
        line.receipt = receipt
        line.purchase_price_snapshot = line.item.average_purchase_rate or Decimal("0.00")
        line.gst_percentage = line.item.gst_percentage or Decimal("0.00")
        if line.item.current_stock < line.quantity:
            raise ValueError(f"Only {line.item.current_stock} units are currently available for {line.item.name}.")
        line.save()
        active_lines.append(line)

    for deleted_line in line_formset.deleted_objects:
        deleted_line.delete()

    receipt.refresh_totals()

    for line in active_lines:
        line.item.refresh_purchase_metrics()
        Inventory.objects.get_or_create(item=line.item)
        line.item.inventory.save()
        record_stock_movement(
            item=line.item,
            movement_type="sale",
            quantity=-line.quantity,
            user=user,
            reference=receipt.receipt_no,
            notes=f"Sold {line.quantity} units at {line.unit_price} per unit.",
        )

    return receipt
