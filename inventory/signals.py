"""
Signals for Inventory Management
Handles automatic low stock alerts and inventory updates
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from inventory.models import Item, Purchase, Inventory, LowStockAlert


@receiver(post_save, sender=Item)
def check_low_stock(sender, instance, created, **kwargs):
    """Create low stock alert if stock falls below minimum"""
    if instance.is_active and instance.current_stock <= instance.minimum_stock:
        # Check if there's already an active alert
        existing_alert = LowStockAlert.objects.filter(
            item=instance,
            status__in=["active", "acknowledged"],
        ).exists()

        if not existing_alert:
            LowStockAlert.objects.create(
                item=instance,
                current_stock=instance.current_stock,
                minimum_stock=instance.minimum_stock,
                status="active",
            )


@receiver(post_save, sender=Purchase)
def update_item_inventory(sender, instance, created, **kwargs):
    """Update item inventory record on purchase save"""
    if created:
        inventory, _ = Inventory.objects.get_or_create(item=instance.item)
        inventory.save()  # Trigger stats update


@receiver(post_save, sender=Item)
def create_inventory_record(sender, instance, created, **kwargs):
    """Create inventory record when item is created"""
    if created:
        Inventory.objects.get_or_create(item=instance)
