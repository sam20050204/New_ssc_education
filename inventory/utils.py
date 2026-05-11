"""
Utilities for Inventory Management
Helper functions and utilities for inventory operations
"""

from decimal import Decimal
from django.db.models import Sum, F, Count, DecimalField
from inventory.models import Item, Purchase, Inventory, LowStockAlert


def get_inventory_summary():
    """Get overall inventory summary statistics"""
    items = Item.objects.filter(is_active=True)

    summary = {
        'total_items': items.count(),
        'total_stock': items.aggregate(
            total=Sum('current_stock', default=0)
        )['total'],
        'total_value': items.aggregate(
            total=Sum(
                F('current_stock') * F('average_purchase_rate'),
                output_field=DecimalField(),
            ),
            default=Decimal('0.00')
        )['total'] or Decimal('0.00'),
        'low_stock_count': items.filter(
            current_stock__lte=F('minimum_stock')
        ).count(),
        'overstocked_count': items.filter(
            current_stock__gt=F('maximum_stock')
        ).count(),
    }

    return summary


def calculate_item_profit_summary(item):
    """Calculate comprehensive profit summary for an item"""
    return {
        'profit_per_unit': item.profit_per_unit,
        'profit_margin_percent': item.profit_margin_percentage,
        'total_profit': item.total_profit,
        'total_value': item.total_value,
        'total_selling_value': item.total_selling_value,
    }


def get_supplier_statistics(supplier):
    """Get comprehensive statistics for a supplier"""
    purchases = supplier.purchases.all()

    stats = {
        'total_purchases': purchases.count(),
        'total_quantity': purchases.aggregate(
            total=Sum('quantity', default=0)
        )['total'],
        'total_spent': purchases.aggregate(
            total=Sum('total_purchase_price', default=Decimal('0.00'))
        )['total'] or Decimal('0.00'),
        'average_order_value': Decimal('0.00'),
    }

    if stats['total_purchases'] > 0:
        stats['average_order_value'] = stats['total_spent'] / stats['total_purchases']

    return stats


def get_category_statistics(category):
    """Get comprehensive statistics for a category"""
    items = category.items.filter(is_active=True)

    stats = {
        'item_count': items.count(),
        'total_stock': items.aggregate(
            total=Sum('current_stock', default=0)
        )['total'],
        'total_value': items.aggregate(
            total=Sum(
                F('current_stock') * F('average_purchase_rate'),
                output_field=DecimalField(),
            ),
            default=Decimal('0.00')
        )['total'] or Decimal('0.00'),
        'total_profit': items.aggregate(
            total=Sum(
                F('current_stock') * (F('selling_price') - F('average_purchase_rate')),
                output_field=DecimalField(),
            ),
            default=Decimal('0.00')
        )['total'] or Decimal('0.00'),
    }

    return stats


def check_and_create_low_stock_alerts():
    """Scan all items and create low stock alerts as needed"""
    items = Item.objects.filter(
        is_active=True,
        current_stock__lte=F('minimum_stock')
    )

    created_count = 0
    for item in items:
        # Check if alert already exists and is active
        existing = LowStockAlert.objects.filter(
            item=item,
            status__in=['active', 'acknowledged']
        ).exists()

        if not existing:
            LowStockAlert.objects.create(
                item=item,
                current_stock=item.current_stock,
                minimum_stock=item.minimum_stock,
            )
            created_count += 1

    return created_count


def get_purchase_price_history(item, limit=10):
    """Get purchase price history for trend analysis"""
    purchases = item.purchases.order_by(
        '-purchase_date'
    ).values(
        'purchase_date',
        'purchase_rate',
        'quantity',
        'supplier__name'
    )[:limit]

    return list(purchases)


def format_currency(amount, symbol='₹'):
    """Format amount as currency"""
    if isinstance(amount, (int, float)):
        amount = Decimal(str(amount))
    return f"{symbol} {amount:,.2f}"


def format_percentage(value):
    """Format value as percentage"""
    if isinstance(value, (int, float)):
        value = Decimal(str(value))
    return f"{value:.2f}%"


def is_item_profitable(item):
    """Check if item is profitable"""
    return item.profit_per_unit > 0


def get_profit_status(item):
    """Get profit status label"""
    profit = item.profit_per_unit
    if profit > 0:
        return 'Profitable'
    elif profit < 0:
        return 'Loss Making'
    else:
        return 'Break Even'


def get_stock_status(item):
    """Get stock status label"""
    if item.current_stock <= item.minimum_stock:
        return 'Low Stock'
    elif item.current_stock > item.maximum_stock:
        return 'Overstocked'
    else:
        return 'Optimal'


def export_items_to_dict(items):
    """Convert items to dictionary for reporting/export"""
    result = []
    for item in items:
        result.append({
            'name': item.name,
            'sku': item.sku,
            'category': item.category.name,
            'stock': item.current_stock,
            'min_stock': item.minimum_stock,
            'max_stock': item.maximum_stock,
            'unit_cost': str(item.average_purchase_rate),
            'unit_price': str(item.selling_price),
            'total_value': str(item.total_value),
            'profit_per_unit': str(item.profit_per_unit),
            'profit_percent': str(item.profit_margin_percentage),
        })
    return result
