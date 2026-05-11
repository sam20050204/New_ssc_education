"""
Initial migration for Inventory module
"""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
from decimal import Decimal


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=100, unique=True)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('icon', models.CharField(blank=True, help_text='Font Awesome icon class', max_length=50, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
            ],
            options={
                'verbose_name': 'Category',
                'verbose_name_plural': 'Categories',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=100)),
                ('contact_person', models.CharField(blank=True, max_length=100, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('phone', models.CharField(blank=True, max_length=20, null=True)),
                ('alternate_phone', models.CharField(blank=True, max_length=20, null=True)),
                ('address', models.TextField(blank=True, null=True)),
                ('city', models.CharField(blank=True, max_length=100, null=True)),
                ('state', models.CharField(blank=True, max_length=100, null=True)),
                ('pincode', models.CharField(blank=True, max_length=10, null=True)),
                ('gst_number', models.CharField(blank=True, max_length=15, null=True, unique=True)),
                ('payment_terms', models.CharField(blank=True, help_text='E.g., Net 30, Net 60, COD', max_length=100, null=True)),
                ('bank_details', models.TextField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('website', models.URLField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
            ],
            options={
                'verbose_name': 'Supplier',
                'verbose_name_plural': 'Suppliers',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=150)),
                ('sku', models.CharField(db_index=True, help_text='Stock Keeping Unit (auto-generated if blank)', max_length=50, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('specifications', models.TextField(blank=True, null=True)),
                ('image', models.ImageField(blank=True, help_text='Product image', null=True, upload_to='inventory/items/')),
                ('current_stock', models.PositiveIntegerField(db_index=True, default=0)),
                ('minimum_stock', models.PositiveIntegerField(default=5, validators=[django.core.validators.MinValueValidator(0)], help_text='Low stock alert threshold')),
                ('maximum_stock', models.PositiveIntegerField(default=100, validators=[django.core.validators.MinValueValidator(1)], help_text='Maximum stock level')),
                ('average_purchase_rate', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Average cost per unit', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('latest_purchase_rate', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Latest purchase cost per unit', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('selling_price', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Current selling price per unit', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('gst_percentage', models.DecimalField(decimal_places=2, default=Decimal('18.00'), help_text='GST percentage', max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='items', to='inventory.category')),
            ],
            options={
                'verbose_name': 'Item',
                'verbose_name_plural': 'Items',
                'ordering': ['-created_at'],
                'unique_together': {('name', 'category')},
            },
        ),
        migrations.CreateModel(
            name='Purchase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('purchase_date', models.DateField(db_index=True)),
                ('quantity', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ('purchase_rate', models.DecimalField(decimal_places=2, help_text='Cost per unit', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('total_purchase_price', models.DecimalField(decimal_places=2, help_text='Total cost = quantity × purchase_rate', max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('selling_price', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Selling price at time of purchase', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('batch_number', models.CharField(blank=True, db_index=True, max_length=100, null=True)),
                ('expiry_date', models.DateField(blank=True, null=True)),
                ('invoice_number', models.CharField(blank=True, db_index=True, max_length=100, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='purchases_created', to=settings.AUTH_USER_MODEL)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='purchases', to='inventory.item')),
                ('supplier', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='purchases', to='inventory.supplier')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='purchases_updated', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Purchase',
                'verbose_name_plural': 'Purchases',
                'ordering': ['-purchase_date', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='StockMovement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('movement_type', models.CharField(choices=[('purchase', 'Purchase'), ('sale', 'Sale'), ('adjustment', 'Adjustment'), ('return', 'Return'), ('damage', 'Damage/Loss')], db_index=True, max_length=20)),
                ('quantity', models.IntegerField(help_text='Negative for reduction', validators=[django.core.validators.MinValueValidator(-9999)])),
                ('reference', models.CharField(blank=True, help_text='Reference ID (Invoice, PO, etc)', max_length=100, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='stock_movements_created', to=settings.AUTH_USER_MODEL)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stock_movements', to='inventory.item')),
            ],
            options={
                'verbose_name': 'Stock Movement',
                'verbose_name_plural': 'Stock Movements',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='LowStockAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('active', 'Active'), ('acknowledged', 'Acknowledged'), ('resolved', 'Resolved')], db_index=True, default='active', max_length=20)),
                ('current_stock', models.PositiveIntegerField()),
                ('minimum_stock', models.PositiveIntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('acknowledged_at', models.DateTimeField(blank=True, null=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('acknowledged_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='acknowledged_alerts', to=settings.AUTH_USER_MODEL)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='low_stock_alerts', to='inventory.item')),
            ],
            options={
                'verbose_name': 'Low Stock Alert',
                'verbose_name_plural': 'Low Stock Alerts',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Inventory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_purchases', models.PositiveIntegerField(default=0, help_text='Total number of purchases')),
                ('total_quantity_purchased', models.PositiveIntegerField(default=0, help_text='Total quantity purchased')),
                ('total_quantity_sold', models.PositiveIntegerField(default=0, help_text='Total quantity sold')),
                ('last_stock_check_date', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('item', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='inventory', to='inventory.item')),
                ('last_stock_check_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inventory_checks', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Inventory',
                'verbose_name_plural': 'Inventories',
            },
        ),
        # Add indexes
        migrations.AddIndex(
            model_name='category',
            index=models.Index(fields=['is_active', '-created_at'], name='inventory_c_is_acti_idx'),
        ),
        migrations.AddIndex(
            model_name='supplier',
            index=models.Index(fields=['is_active', '-created_at'], name='inventory_s_is_acti_idx'),
        ),
        migrations.AddIndex(
            model_name='item',
            index=models.Index(fields=['category', 'is_active'], name='inventory_i_categor_idx'),
        ),
        migrations.AddIndex(
            model_name='item',
            index=models.Index(fields=['is_active', '-created_at'], name='inventory_i_is_acti_idx'),
        ),
        migrations.AddIndex(
            model_name='item',
            index=models.Index(fields=['current_stock'], name='inventory_i_current_idx'),
        ),
        migrations.AddIndex(
            model_name='item',
            index=models.Index(fields=['current_stock', 'minimum_stock'], name='low_stock_idx'),
        ),
        migrations.AddIndex(
            model_name='purchase',
            index=models.Index(fields=['item', '-purchase_date'], name='inventory_p_item_id_idx'),
        ),
        migrations.AddIndex(
            model_name='purchase',
            index=models.Index(fields=['supplier', '-purchase_date'], name='inventory_p_supplier_idx'),
        ),
        migrations.AddIndex(
            model_name='purchase',
            index=models.Index(fields=['-purchase_date'], name='inventory_p_purchase_idx'),
        ),
        migrations.AddIndex(
            model_name='purchase',
            index=models.Index(fields=['batch_number'], name='inventory_p_batch_idx'),
        ),
        migrations.AddIndex(
            model_name='stockmovement',
            index=models.Index(fields=['item', '-created_at'], name='inventory_s_item_id_idx'),
        ),
        migrations.AddIndex(
            model_name='stockmovement',
            index=models.Index(fields=['movement_type', '-created_at'], name='inventory_s_movement_idx'),
        ),
        migrations.AddIndex(
            model_name='lowstockalert',
            index=models.Index(fields=['status', '-created_at'], name='inventory_l_status_idx'),
        ),
        migrations.AddIndex(
            model_name='lowstockalert',
            index=models.Index(fields=['item', 'status'], name='inventory_l_item_id_idx'),
        ),
    ]
