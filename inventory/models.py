"""
Inventory Models - Sales & Inventory Management
Handles categories, suppliers, items, purchases, and inventory tracking
"""

from decimal import Decimal
from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, DecimalValidator
from django.utils import timezone
from django.utils.text import slugify
from django.db.models import Sum, Avg, Q


class Category(models.Model):
    """Product categories for inventory items"""

    name = models.CharField(max_length=100, unique=True, db_index=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True, help_text="Font Awesome icon class")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        indexes = [models.Index(fields=["is_active", "-created_at"])]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Auto-generate slug"""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_item_count(self):
        """Get total items in this category"""
        return self.items.filter(is_active=True).count()

    def get_total_stock(self):
        """Get total quantity in stock for this category"""
        return (
            self.items.filter(is_active=True).aggregate(
                total=Sum("current_stock", default=0)
            )["total"]
            or 0
        )

    def get_total_value(self):
        """Get total inventory value for this category"""
        return (
            self.items.filter(is_active=True).aggregate(
                total=Sum(
                    models.F("current_stock") * models.F("average_purchase_rate"),
                    output_field=models.DecimalField(),
                    default=Decimal("0.00"),
                )
            )["total"]
            or Decimal("0.00")
        )


class Supplier(models.Model):
    """Supplier/Vendor information"""

    name = models.CharField(max_length=100, db_index=True)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    alternate_phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)

    gst_number = models.CharField(max_length=15, blank=True, null=True, unique=True)
    payment_terms = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="E.g., Net 30, Net 60, COD",
    )
    bank_details = models.TextField(blank=True, null=True)

    notes = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Supplier"
        verbose_name_plural = "Suppliers"
        indexes = [models.Index(fields=["is_active", "-created_at"])]

    def __str__(self):
        return self.name

    def get_purchase_count(self):
        """Get total purchases from this supplier"""
        return self.purchases.count()

    def get_total_spent(self):
        """Get total amount spent with this supplier"""
        return (
            self.purchases.aggregate(
                total=Sum("total_purchase_price", default=Decimal("0.00"))
            )["total"]
            or Decimal("0.00")
        )


class Item(models.Model):
    """Inventory item/product"""

    name = models.CharField(max_length=150, db_index=True)
    sku = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Stock Keeping Unit (auto-generated if blank)",
    )
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="items"
    )

    description = models.TextField(blank=True, null=True)
    specifications = models.TextField(blank=True, null=True)
    image = models.ImageField(
        upload_to="inventory/items/",
        blank=True,
        null=True,
        help_text="Product image",
    )

    # Stock Information
    current_stock = models.PositiveIntegerField(default=0, db_index=True)
    minimum_stock = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(0)],
        help_text="Low stock alert threshold",
    )
    maximum_stock = models.PositiveIntegerField(
        default=100,
        validators=[MinValueValidator(1)],
        help_text="Maximum stock level",
    )

    # Pricing Information
    average_purchase_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Average cost per unit",
    )
    latest_purchase_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Latest purchase cost per unit",
    )
    selling_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Current selling price per unit",
    )
    gst_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("18.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="GST percentage",
    )

    # Status
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Item"
        verbose_name_plural = "Items"
        unique_together = ["name", "category"]
        indexes = [
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["is_active", "-created_at"]),
            models.Index(fields=["current_stock"]),
            models.Index(
                fields=["current_stock", "minimum_stock"],
                name="low_stock_idx",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    def save(self, *args, **kwargs):
        """Auto-generate SKU if not provided"""
        if not self.sku:
            # Generate SKU from category slug and name
            base_sku = f"{self.category.slug[:3]}{slugify(self.name)[:8]}"
            base_sku = base_sku.upper()
            sku = base_sku
            counter = 1
            while Item.objects.filter(sku=sku).exclude(pk=self.pk).exists():
                sku = f"{base_sku}{counter}"
                counter += 1
            self.sku = sku
        super().save(*args, **kwargs)

    @property
    def is_low_stock(self):
        """Check if stock is below minimum level"""
        return self.current_stock <= self.minimum_stock

    @property
    def is_overstocked(self):
        """Check if stock exceeds maximum level"""
        return self.current_stock > self.maximum_stock

    @property
    def profit_per_unit(self):
        """Calculate profit per unit"""
        if self.selling_price and self.average_purchase_rate:
            return self.selling_price - self.average_purchase_rate
        return Decimal("0.00")

    @property
    def profit_margin_percentage(self):
        """Calculate profit margin percentage"""
        if self.average_purchase_rate and self.average_purchase_rate > 0:
            return (
                (self.profit_per_unit / self.average_purchase_rate) * 100
            )
        return Decimal("0.00")

    @property
    def total_value(self):
        """Calculate total inventory value at average purchase rate"""
        return self.current_stock * self.average_purchase_rate

    @property
    def total_selling_value(self):
        """Calculate total potential revenue if all stock sold"""
        return self.current_stock * self.selling_price

    @property
    def total_profit(self):
        """Calculate total expected profit from current stock"""
        return self.current_stock * self.profit_per_unit

    def get_recent_purchases(self, limit=5):
        """Get recent purchases of this item"""
        return self.purchases.select_related("supplier").order_by(
            "-purchase_date"
        )[:limit]

    def update_average_price(self):
        """Recalculate average purchase rate from all purchases"""
        total_cost = self.purchases.aggregate(
            total=Sum("total_purchase_price", default=Decimal("0.00"))
        )["total"]
        total_quantity = self.purchases.aggregate(
            total=Sum("quantity", default=0)
        )["total"]

        if total_quantity > 0:
            self.average_purchase_rate = Decimal(total_cost) / Decimal(
                total_quantity
            )
            self.save(update_fields=["average_purchase_rate"])

    def refresh_purchase_metrics(self, save=True):
        """Synchronize stock and pricing snapshots from purchase history."""
        summary = self.purchases.aggregate(
            total_cost=Sum("total_purchase_price", default=Decimal("0.00")),
            total_quantity=Sum("quantity", default=0),
        )
        latest_purchase = self.purchases.order_by(
            "-purchase_date", "-created_at"
        ).first()

        total_quantity = summary["total_quantity"] or 0
        total_cost = summary["total_cost"] or Decimal("0.00")

        self.current_stock = total_quantity
        self.latest_purchase_rate = (
            latest_purchase.purchase_rate if latest_purchase else Decimal("0.00")
        )
        self.average_purchase_rate = (
            Decimal(total_cost) / Decimal(total_quantity)
            if total_quantity
            else Decimal("0.00")
        )

        if save:
            self.save(
                update_fields=[
                    "current_stock",
                    "latest_purchase_rate",
                    "average_purchase_rate",
                    "updated_at",
                ]
            )
        return self


class Purchase(models.Model):
    """Purchase history and batch tracking"""

    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name="purchases"
    )
    supplier = models.ForeignKey(
        Supplier, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="purchases"
    )

    purchase_date = models.DateField(default=timezone.now, db_index=True)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    purchase_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Cost per unit",
    )
    total_purchase_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Total cost = quantity × purchase_rate",
    )

    selling_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Selling price at time of purchase",
    )

    # Batch tracking
    batch_number = models.CharField(
        max_length=100, blank=True, null=True, db_index=True
    )
    expiry_date = models.DateField(blank=True, null=True)

    # Additional info
    invoice_number = models.CharField(
        max_length=100, blank=True, null=True, db_index=True
    )
    notes = models.TextField(blank=True, null=True)

    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="purchases_created",
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="purchases_updated",
    )

    class Meta:
        ordering = ["-purchase_date", "-created_at"]
        verbose_name = "Purchase"
        verbose_name_plural = "Purchases"
        indexes = [
            models.Index(fields=["item", "-purchase_date"]),
            models.Index(fields=["supplier", "-purchase_date"]),
            models.Index(fields=["-purchase_date"]),
            models.Index(fields=["batch_number"]),
        ]

    def __str__(self):
        return f"{self.item.name} - {self.quantity} units on {self.purchase_date}"

    def save(self, *args, **kwargs):
        """Calculate total purchase price and synchronize item inventory."""
        self.total_purchase_price = self.quantity * self.purchase_rate
        previous_item = None

        if self.pk:
            previous_item = Purchase.objects.select_related("item").get(pk=self.pk).item

        super().save(*args, **kwargs)

        if previous_item and previous_item.pk != self.item.pk:
            previous_item.refresh_purchase_metrics()
        self.item.refresh_purchase_metrics()

    def delete(self, *args, **kwargs):
        """Handle stock recalculation on purchase deletion."""
        item = self.item
        super().delete(*args, **kwargs)
        item.refresh_purchase_metrics()


class Inventory(models.Model):
    """Stock and inventory tracking"""

    item = models.OneToOneField(
        Item, on_delete=models.CASCADE, related_name="inventory"
    )

    total_purchases = models.PositiveIntegerField(
        default=0, help_text="Total number of purchases"
    )
    total_quantity_purchased = models.PositiveIntegerField(
        default=0, help_text="Total quantity purchased"
    )
    total_quantity_sold = models.PositiveIntegerField(
        default=0, help_text="Total quantity sold"
    )

    last_stock_check_date = models.DateTimeField(null=True, blank=True)
    last_stock_check_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inventory_checks",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Inventory"
        verbose_name_plural = "Inventories"

    def __str__(self):
        return f"Inventory - {self.item.name}"

    def save(self, *args, **kwargs):
        """Update inventory statistics"""
        if self.pk:
            # Update totals from purchases
            self.total_purchases = self.item.purchases.count()
            self.total_quantity_purchased = (
                self.item.purchases.aggregate(
                    total=Sum("quantity", default=0)
                )["total"]
                or 0
            )
        super().save(*args, **kwargs)

    def get_stock_value(self):
        """Get total value of current stock"""
        return self.item.total_value

    def get_potential_revenue(self):
        """Get potential revenue if all stock is sold"""
        return self.item.total_selling_value


class StockMovement(models.Model):
    """Track stock movements (purchases, sales, adjustments)"""

    MOVEMENT_TYPE_CHOICES = [
        ("purchase", "Purchase"),
        ("sale", "Sale"),
        ("adjustment", "Adjustment"),
        ("return", "Return"),
        ("damage", "Damage/Loss"),
    ]

    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name="stock_movements"
    )
    movement_type = models.CharField(
        max_length=20, choices=MOVEMENT_TYPE_CHOICES, db_index=True
    )
    quantity = models.IntegerField(
        validators=[MinValueValidator(-9999)], help_text="Negative for reduction"
    )
    reference = models.CharField(
        max_length=100, blank=True, null=True, help_text="Reference ID (Invoice, PO, etc)"
    )
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_movements_created",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Stock Movement"
        verbose_name_plural = "Stock Movements"
        indexes = [
            models.Index(fields=["item", "-created_at"]),
            models.Index(fields=["movement_type", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.item.name} ({self.quantity})"


class LowStockAlert(models.Model):
    """Track low stock alerts"""

    STATUS_CHOICES = [
        ("active", "Active"),
        ("acknowledged", "Acknowledged"),
        ("resolved", "Resolved"),
    ]

    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name="low_stock_alerts"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="active", db_index=True
    )
    current_stock = models.PositiveIntegerField()
    minimum_stock = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="acknowledged_alerts",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Low Stock Alert"
        verbose_name_plural = "Low Stock Alerts"
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["item", "status"]),
        ]

    def __str__(self):
        return f"Low Stock Alert - {self.item.name} ({self.current_stock}/{self.minimum_stock})"
