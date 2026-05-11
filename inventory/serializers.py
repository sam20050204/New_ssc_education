"""
Serializers for Inventory API
JSON serialization for API endpoints and exports
"""

from rest_framework import serializers
from inventory.models import (
    Category,
    Supplier,
    Item,
    Purchase,
    Inventory,
    StockMovement,
    LowStockAlert,
)


class CategorySerializer(serializers.ModelSerializer):
    item_count = serializers.SerializerMethodField()
    total_stock = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'icon',
            'item_count',
            'total_stock',
            'is_active',
            'created_at',
            'updated_at',
        ]

    def get_item_count(self, obj):
        return obj.get_item_count()

    def get_total_stock(self, obj):
        return obj.get_total_stock()


class SupplierSerializer(serializers.ModelSerializer):
    purchase_count = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()

    class Meta:
        model = Supplier
        fields = [
            'id',
            'name',
            'contact_person',
            'email',
            'phone',
            'alternate_phone',
            'address',
            'city',
            'state',
            'pincode',
            'gst_number',
            'payment_terms',
            'website',
            'purchase_count',
            'total_spent',
            'is_active',
            'created_at',
            'updated_at',
        ]

    def get_purchase_count(self, obj):
        return obj.get_purchase_count()

    def get_total_spent(self, obj):
        return str(obj.get_total_spent())


class ItemListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    profit_per_unit = serializers.SerializerMethodField()
    stock_status = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = [
            'id',
            'name',
            'sku',
            'category',
            'category_name',
            'current_stock',
            'selling_price',
            'average_purchase_rate',
            'profit_per_unit',
            'stock_status',
            'is_active',
        ]

    def get_profit_per_unit(self, obj):
        return str(obj.profit_per_unit)

    def get_stock_status(self, obj):
        if obj.is_low_stock:
            return 'LOW'
        elif obj.is_overstocked:
            return 'OVER'
        return 'OK'


class ItemDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    profit_per_unit = serializers.SerializerMethodField()
    profit_margin_percentage = serializers.SerializerMethodField()
    total_value = serializers.SerializerMethodField()
    total_selling_value = serializers.SerializerMethodField()
    total_profit = serializers.SerializerMethodField()
    stock_status = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = [
            'id',
            'name',
            'sku',
            'category',
            'category_name',
            'description',
            'specifications',
            'current_stock',
            'minimum_stock',
            'maximum_stock',
            'selling_price',
            'average_purchase_rate',
            'latest_purchase_rate',
            'gst_percentage',
            'profit_per_unit',
            'profit_margin_percentage',
            'total_value',
            'total_selling_value',
            'total_profit',
            'stock_status',
            'is_active',
            'created_at',
            'updated_at',
        ]

    def get_profit_per_unit(self, obj):
        return str(obj.profit_per_unit)

    def get_profit_margin_percentage(self, obj):
        return str(obj.profit_margin_percentage)

    def get_total_value(self, obj):
        return str(obj.total_value)

    def get_total_selling_value(self, obj):
        return str(obj.total_selling_value)

    def get_total_profit(self, obj):
        return str(obj.total_profit)

    def get_stock_status(self, obj):
        if obj.is_low_stock:
            return 'LOW'
        elif obj.is_overstocked:
            return 'OVER'
        return 'OK'


class PurchaseListSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )

    class Meta:
        model = Purchase
        fields = [
            'id',
            'item',
            'item_name',
            'supplier',
            'supplier_name',
            'purchase_date',
            'quantity',
            'purchase_rate',
            'total_purchase_price',
            'selling_price',
            'invoice_number',
            'batch_number',
            'created_by_name',
            'created_at',
        ]


class PurchaseDetailSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    updated_by_name = serializers.CharField(
        source='updated_by.get_full_name',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = Purchase
        fields = [
            'id',
            'item',
            'item_name',
            'supplier',
            'supplier_name',
            'purchase_date',
            'quantity',
            'purchase_rate',
            'total_purchase_price',
            'selling_price',
            'batch_number',
            'expiry_date',
            'invoice_number',
            'notes',
            'created_by_name',
            'created_at',
            'updated_by_name',
            'updated_at',
        ]


class InventorySerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    stock_value = serializers.SerializerMethodField()
    potential_revenue = serializers.SerializerMethodField()

    class Meta:
        model = Inventory
        fields = [
            'id',
            'item',
            'item_name',
            'total_purchases',
            'total_quantity_purchased',
            'total_quantity_sold',
            'stock_value',
            'potential_revenue',
            'created_at',
            'updated_at',
        ]

    def get_stock_value(self, obj):
        return str(obj.get_stock_value())

    def get_potential_revenue(self, obj):
        return str(obj.get_potential_revenue())


class StockMovementSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )

    class Meta:
        model = StockMovement
        fields = [
            'id',
            'item',
            'item_name',
            'movement_type',
            'quantity',
            'reference',
            'notes',
            'created_by_name',
            'created_at',
        ]


class LowStockAlertSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    acknowledged_by_name = serializers.CharField(
        source='acknowledged_by.get_full_name',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = LowStockAlert
        fields = [
            'id',
            'item',
            'item_name',
            'current_stock',
            'minimum_stock',
            'status',
            'created_at',
            'acknowledged_at',
            'acknowledged_by_name',
            'resolved_at',
        ]


class DashboardSummarySerializer(serializers.Serializer):
    """Serializer for dashboard summary data"""
    total_items = serializers.IntegerField()
    total_categories = serializers.IntegerField()
    total_suppliers = serializers.IntegerField()
    total_purchases = serializers.IntegerField()
    low_stock_items = serializers.IntegerField()
    overstocked_items = serializers.IntegerField()
    total_inventory_value = serializers.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    total_selling_value = serializers.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    total_potential_profit = serializers.DecimalField(
        max_digits=12,
        decimal_places=2
    )
