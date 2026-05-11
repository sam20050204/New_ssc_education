"""
Unit Tests for Inventory Management Module
Test models, views, and business logic
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal

from inventory.models import (
    Category,
    Supplier,
    Item,
    Purchase,
    Inventory,
    LowStockAlert,
)
from inventory.forms import ItemForm, CategoryForm, SupplierForm, PurchaseForm


class CategoryModelTest(TestCase):
    """Test Category model"""

    def setUp(self):
        self.category = Category.objects.create(
            name="Laptops",
            description="Laptop computers",
            icon="fa-laptop"
        )

    def test_category_creation(self):
        """Test category is created correctly"""
        self.assertEqual(self.category.name, "Laptops")
        self.assertTrue(self.category.is_active)

    def test_category_slug_generation(self):
        """Test slug is auto-generated"""
        self.assertEqual(self.category.slug, "laptops")

    def test_category_str(self):
        """Test string representation"""
        self.assertEqual(str(self.category), "Laptops")

    def test_duplicate_category_prevention(self):
        """Test duplicate categories are prevented"""
        with self.assertRaises(Exception):
            Category.objects.create(name="Laptops")


class SupplierModelTest(TestCase):
    """Test Supplier model"""

    def setUp(self):
        self.supplier = Supplier.objects.create(
            name="Dell India",
            contact_person="John Doe",
            email="john@dell.com",
            phone="9876543210",
            city="Mumbai",
            state="Maharashtra",
            gst_number="27AABDA1234H1Z0"
        )

    def test_supplier_creation(self):
        """Test supplier is created correctly"""
        self.assertEqual(self.supplier.name, "Dell India")
        self.assertTrue(self.supplier.is_active)

    def test_supplier_str(self):
        """Test string representation"""
        self.assertEqual(str(self.supplier), "Dell India")


class ItemModelTest(TestCase):
    """Test Item model"""

    def setUp(self):
        self.category = Category.objects.create(name="Laptops")
        self.item = Item.objects.create(
            name="Dell XPS 13",
            category=self.category,
            selling_price=Decimal("80000.00"),
            minimum_stock=5,
            maximum_stock=50
        )

    def test_item_creation(self):
        """Test item is created correctly"""
        self.assertEqual(self.item.name, "Dell XPS 13")
        self.assertEqual(self.item.current_stock, 0)

    def test_sku_auto_generation(self):
        """Test SKU is auto-generated"""
        self.assertIsNotNone(self.item.sku)
        self.assertTrue(self.item.sku.startswith("LAP"))

    def test_low_stock_property(self):
        """Test low stock detection"""
        self.item.current_stock = 3
        self.assertTrue(self.item.is_low_stock)

    def test_overstocked_property(self):
        """Test overstocked detection"""
        self.item.current_stock = 60
        self.assertTrue(self.item.is_overstocked)

    def test_profit_calculation(self):
        """Test profit per unit calculation"""
        self.item.average_purchase_rate = Decimal("60000.00")
        profit = self.item.profit_per_unit
        self.assertEqual(profit, Decimal("20000.00"))

    def test_profit_margin_calculation(self):
        """Test profit margin percentage calculation"""
        self.item.average_purchase_rate = Decimal("60000.00")
        margin = self.item.profit_margin_percentage
        expected = (Decimal("20000.00") / Decimal("60000.00")) * 100
        self.assertAlmostEqual(float(margin), float(expected), places=2)


class PurchaseModelTest(TestCase):
    """Test Purchase model"""

    def setUp(self):
        self.category = Category.objects.create(name="Laptops")
        self.item = Item.objects.create(
            name="Dell XPS 13",
            category=self.category,
            selling_price=Decimal("80000.00")
        )
        self.supplier = Supplier.objects.create(
            name="Dell India"
        )
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass"
        )

    def test_purchase_creation(self):
        """Test purchase is created correctly"""
        purchase = Purchase.objects.create(
            item=self.item,
            supplier=self.supplier,
            quantity=5,
            purchase_rate=Decimal("60000.00"),
            total_purchase_price=Decimal("300000.00"),
            created_by=self.user
        )
        self.assertEqual(purchase.quantity, 5)
        self.assertEqual(purchase.item.current_stock, 5)

    def test_total_purchase_price_calculation(self):
        """Test total purchase price is calculated"""
        purchase = Purchase.objects.create(
            item=self.item,
            supplier=self.supplier,
            quantity=10,
            purchase_rate=Decimal("60000.00"),
            created_by=self.user
        )
        expected_total = Decimal("10") * Decimal("60000.00")
        self.assertEqual(purchase.total_purchase_price, expected_total)

    def test_stock_update_on_purchase(self):
        """Test stock updates when purchase is created"""
        initial_stock = self.item.current_stock
        Purchase.objects.create(
            item=self.item,
            supplier=self.supplier,
            quantity=5,
            purchase_rate=Decimal("60000.00"),
            created_by=self.user
        )
        self.item.refresh_from_db()
        self.assertEqual(self.item.current_stock, initial_stock + 5)

    def test_purchase_deletion_reduces_stock(self):
        """Test stock reduces when purchase is deleted"""
        purchase = Purchase.objects.create(
            item=self.item,
            supplier=self.supplier,
            quantity=5,
            purchase_rate=Decimal("60000.00"),
            created_by=self.user
        )
        self.assertEqual(self.item.current_stock, 5)
        purchase.delete()
        self.item.refresh_from_db()
        self.assertEqual(self.item.current_stock, 0)


class LowStockAlertModelTest(TestCase):
    """Test LowStockAlert model"""

    def setUp(self):
        self.category = Category.objects.create(name="Laptops")
        self.item = Item.objects.create(
            name="Dell XPS 13",
            category=self.category,
            selling_price=Decimal("80000.00"),
            minimum_stock=10,
            current_stock=5
        )

    def test_alert_creation(self):
        """Test alert is created when stock is low"""
        alert = LowStockAlert.objects.create(
            item=self.item,
            current_stock=5,
            minimum_stock=10
        )
        self.assertEqual(alert.status, "active")

    def test_alert_resolution(self):
        """Test alert can be resolved"""
        alert = LowStockAlert.objects.create(
            item=self.item,
            current_stock=5,
            minimum_stock=10
        )
        alert.status = "resolved"
        alert.save()
        self.assertEqual(alert.status, "resolved")


class CategoryFormTest(TestCase):
    """Test CategoryForm"""

    def test_valid_form(self):
        """Test valid category form"""
        form = CategoryForm(data={
            'name': 'Laptops',
            'description': 'Laptop computers',
            'icon': 'fa-laptop'
        })
        self.assertTrue(form.is_valid())

    def test_duplicate_category_validation(self):
        """Test duplicate category validation"""
        Category.objects.create(name="Laptops")
        form = CategoryForm(data={
            'name': 'Laptops',
            'description': 'Another laptop category',
        })
        self.assertFalse(form.is_valid())

    def test_empty_name_validation(self):
        """Test empty name validation"""
        form = CategoryForm(data={
            'name': '',
            'description': 'Test',
        })
        self.assertFalse(form.is_valid())


class InventoryViewTest(TestCase):
    """Test Inventory Views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.client.login(username='testuser', password='testpass')

        self.category = Category.objects.create(name="Laptops")
        self.item = Item.objects.create(
            name="Dell XPS 13",
            category=self.category,
            selling_price=Decimal("80000.00")
        )

    def test_dashboard_view(self):
        """Test dashboard view"""
        response = self.client.get(reverse('inventory:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('total_items', response.context)

    def test_item_list_view(self):
        """Test item list view"""
        response = self.client.get(reverse('inventory:item-list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('items', response.context)

    def test_item_detail_view(self):
        """Test item detail view"""
        response = self.client.get(
            reverse('inventory:item-detail', args=[self.item.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['item'], self.item)

    def test_category_list_view(self):
        """Test category list view"""
        response = self.client.get(reverse('inventory:category-list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('categories', response.context)

    def test_add_item_view_get(self):
        """Test add item view GET request"""
        response = self.client.get(reverse('inventory:add-item'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('item_form', response.context)

    def test_add_item_view_post(self):
        """Test add item view POST request"""
        data = {
            'name': 'HP Pavilion 15',
            'category': self.category.id,
            'selling_price': Decimal('50000.00'),
            'minimum_stock': 5,
            'maximum_stock': 50,
            'gst_percentage': Decimal('18.00'),
            'supplier': '',
            'purchase_date': '2024-05-11',
            'quantity': 10,
            'purchase_rate': Decimal('40000.00'),
        }
        response = self.client.post(reverse('inventory:add-item'), data)
        self.assertEqual(response.status_code, 302)  # Redirect on success

    def test_login_required(self):
        """Test login is required"""
        self.client.logout()
        response = self.client.get(reverse('inventory:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login


class InventoryUtilsTest(TestCase):
    """Test utility functions"""

    def setUp(self):
        self.category = Category.objects.create(name="Laptops")
        self.item = Item.objects.create(
            name="Dell XPS 13",
            category=self.category,
            selling_price=Decimal("80000.00"),
            average_purchase_rate=Decimal("60000.00"),
            current_stock=10
        )

    def test_profit_summary(self):
        """Test profit summary calculation"""
        profit_per_unit = self.item.profit_per_unit
        self.assertEqual(profit_per_unit, Decimal("20000.00"))

    def test_item_profitable_check(self):
        """Test item profitability check"""
        is_profitable = self.item.profit_per_unit > 0
        self.assertTrue(is_profitable)

    def test_total_value_calculation(self):
        """Test total inventory value"""
        total_value = self.item.total_value
        expected = 10 * Decimal("60000.00")
        self.assertEqual(total_value, expected)
