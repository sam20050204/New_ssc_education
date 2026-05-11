"""
Django Admin Configuration for Inventory
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, F, DecimalField

from inventory.models import (
    Category,
    Supplier,
    Item,
    Purchase,
    Inventory,
    StockMovement,
    LowStockAlert,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "item_count", "total_stock", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            "Basic Info",
            {
                "fields": ("name", "slug", "description", "icon")
            },
        ),
        (
            "Status",
            {
                "fields": ("is_active",)
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def item_count(self, obj):
        return obj.get_item_count()
    item_count.short_description = "Items"

    def total_stock(self, obj):
        return obj.get_total_stock()
    total_stock.short_description = "Total Stock"


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "contact_person",
        "phone",
        "purchase_count",
        "total_spent",
        "is_active",
    )
    list_filter = ("is_active", "city", "state", "created_at")
    search_fields = ("name", "email", "phone", "gst_number")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            "Basic Info",
            {
                "fields": ("name", "contact_person", "email", "phone", "alternate_phone")
            },
        ),
        (
            "Address",
            {
                "fields": ("address", "city", "state", "pincode")
            },
        ),
        (
            "Business Details",
            {
                "fields": ("gst_number", "payment_terms", "website")
            },
        ),
        (
            "Banking",
            {
                "fields": ("bank_details",),
                "classes": ("collapse",),
            },
        ),
        (
            "Additional",
            {
                "fields": ("notes", "is_active")
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def purchase_count(self, obj):
        return obj.get_purchase_count()
    purchase_count.short_description = "Purchases"

    def total_spent(self, obj):
        return f"₹ {obj.get_total_spent():.2f}"
    total_spent.short_description = "Total Spent"


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "sku",
        "category",
        "stock_status",
        "current_stock",
        "selling_price",
        "profit_margin",
        "is_active",
    )
    list_filter = (
        "category",
        "is_active",
        "created_at",
    )
    search_fields = ("name", "sku", "category__name")
    readonly_fields = (
        "sku",
        "average_purchase_rate",
        "latest_purchase_rate",
        "total_value",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Basic Info",
            {
                "fields": ("name", "sku", "category", "description", "specifications", "image")
            },
        ),
        (
            "Stock Management",
            {
                "fields": (
                    "current_stock",
                    "minimum_stock",
                    "maximum_stock",
                )
            },
        ),
        (
            "Pricing",
            {
                "fields": (
                    "average_purchase_rate",
                    "latest_purchase_rate",
                    "selling_price",
                    "gst_percentage",
                    "total_value",
                )
            },
        ),
        (
            "Status",
            {
                "fields": ("is_active",)
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def stock_status(self, obj):
        if obj.current_stock <= obj.minimum_stock:
            return format_html(
                '<span style="color: red; font-weight: bold;">LOW</span>'
            )
        elif obj.current_stock > obj.maximum_stock:
            return format_html(
                '<span style="color: orange; font-weight: bold;">OVER</span>'
            )
        return format_html(
            '<span style="color: green; font-weight: bold;">OK</span>'
        )
    stock_status.short_description = "Status"

    def profit_margin(self, obj):
        margin = obj.profit_margin_percentage
        color = "green" if margin > 0 else "red"
        return format_html(
            f'<span style="color: {color};">{margin:.2f}%</span>'
        )
    profit_margin.short_description = "Profit Margin"


class PurchaseInline(admin.TabularInline):
    model = Purchase
    extra = 0
    readonly_fields = ("total_purchase_price", "created_at", "created_by")
    fields = (
        "supplier",
        "purchase_date",
        "quantity",
        "purchase_rate",
        "total_purchase_price",
        "invoice_number",
    )


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = (
        "item",
        "supplier",
        "purchase_date",
        "quantity",
        "purchase_rate",
        "total_price",
        "created_by",
    )
    list_filter = ("purchase_date", "supplier", "created_at")
    search_fields = ("item__name", "supplier__name", "invoice_number")
    readonly_fields = ("total_purchase_price", "created_at", "updated_at")
    date_hierarchy = "purchase_date"

    fieldsets = (
        (
            "Purchase Details",
            {
                "fields": ("item", "supplier", "purchase_date", "invoice_number")
            },
        ),
        (
            "Quantity & Pricing",
            {
                "fields": ("quantity", "purchase_rate", "total_purchase_price", "selling_price")
            },
        ),
        (
            "Batch & Tracking",
            {
                "fields": ("batch_number", "expiry_date"),
            },
        ),
        (
            "Notes",
            {
                "fields": ("notes",),
                "classes": ("collapse",),
            },
        ),
        (
            "Audit Trail",
            {
                "fields": ("created_by", "created_at", "updated_by", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def total_price(self, obj):
        return f"₹ {obj.total_purchase_price:.2f}"
    total_price.short_description = "Total Price"


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = (
        "item",
        "total_quantity_purchased",
        "total_quantity_sold",
        "current_stock",
        "stock_value",
    )
    readonly_fields = (
        "total_purchases",
        "total_quantity_purchased",
        "created_at",
        "updated_at",
    )
    search_fields = ("item__name", "item__sku")

    fieldsets = (
        (
            "Item",
            {
                "fields": ("item",)
            },
        ),
        (
            "Stock Statistics",
            {
                "fields": (
                    "total_purchases",
                    "total_quantity_purchased",
                    "total_quantity_sold",
                )
            },
        ),
        (
            "Last Check",
            {
                "fields": ("last_stock_check_date", "last_stock_check_by"),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def current_stock(self, obj):
        return obj.item.current_stock
    current_stock.short_description = "Current Stock"

    def stock_value(self, obj):
        return f"₹ {obj.get_stock_value():.2f}"
    stock_value.short_description = "Stock Value"


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = (
        "item",
        "movement_type",
        "quantity",
        "reference",
        "created_by",
        "created_at",
    )
    list_filter = ("movement_type", "created_at")
    search_fields = ("item__name", "reference")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"


@admin.register(LowStockAlert)
class LowStockAlertAdmin(admin.ModelAdmin):
    list_display = (
        "item",
        "current_stock",
        "minimum_stock",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("item__name",)
    readonly_fields = ("created_at", "acknowledged_at", "resolved_at")
