"""
Management command to initialize sample data for inventory module
Usage: python manage.py init_inventory_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from decimal import Decimal
from inventory.models import Category, Supplier, Item, Purchase
from django.utils import timezone


class Command(BaseCommand):
    help = 'Initialize sample data for inventory module'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before creating new data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            Category.objects.all().delete()
            Supplier.objects.all().delete()
            Item.objects.all().delete()
            Purchase.objects.all().delete()

        self.stdout.write(self.style.SUCCESS('Creating sample data...'))

        # Create categories
        categories_data = [
            {
                'name': 'Laptops',
                'description': 'Portable computers and notebooks',
                'icon': 'fa-laptop'
            },
            {
                'name': 'Desktops',
                'description': 'Desktop computers and workstations',
                'icon': 'fa-desktop'
            },
            {
                'name': 'Peripherals',
                'description': 'Keyboard, mouse, monitor, and other accessories',
                'icon': 'fa-keyboard'
            },
            {
                'name': 'Components',
                'description': 'RAM, SSD, HDD, Graphics Cards, CPUs',
                'icon': 'fa-microchip'
            },
            {
                'name': 'Services',
                'description': 'Repair and maintenance services',
                'icon': 'fa-tools'
            },
        ]

        categories = {}
        for cat_data in categories_data:
            cat, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description'],
                    'icon': cat_data['icon']
                }
            )
            categories[cat_data['name']] = cat
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created category: {cat.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'→ Category already exists: {cat.name}')
                )

        # Create suppliers
        suppliers_data = [
            {
                'name': 'Dell India',
                'contact_person': 'Sales Team',
                'email': 'sales@dell.com',
                'phone': '9876543210',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'gst_number': '27AABDA1234H1Z0',
                'payment_terms': 'Net 30'
            },
            {
                'name': 'HP India',
                'contact_person': 'Procurement',
                'email': 'procurement@hp.com',
                'phone': '9123456789',
                'city': 'Bangalore',
                'state': 'Karnataka',
                'gst_number': '29AABDA5678H1Z0',
                'payment_terms': 'Net 45'
            },
            {
                'name': 'Lenovo India',
                'contact_person': 'Business Manager',
                'email': 'business@lenovo.com',
                'phone': '8765432109',
                'city': 'Delhi',
                'state': 'Delhi',
                'gst_number': '07AABDA9012H1Z0',
                'payment_terms': 'COD'
            },
            {
                'name': 'ASUS India',
                'contact_person': 'Account Manager',
                'email': 'accounts@asus.com',
                'phone': '9988776655',
                'city': 'Hyderabad',
                'state': 'Telangana',
                'gst_number': '36AABDA3456H1Z0',
                'payment_terms': 'Net 30'
            },
        ]

        suppliers = {}
        for supp_data in suppliers_data:
            supp, created = Supplier.objects.get_or_create(
                name=supp_data['name'],
                defaults={k: v for k, v in supp_data.items() if k != 'name'}
            )
            suppliers[supp_data['name']] = supp
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created supplier: {supp.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'→ Supplier already exists: {supp.name}')
                )

        # Create items with purchases
        items_data = [
            {
                'name': 'Dell XPS 13',
                'category': 'Laptops',
                'selling_price': Decimal('95000.00'),
                'minimum_stock': 3,
                'maximum_stock': 20,
                'purchases': [
                    {
                        'supplier': 'Dell India',
                        'quantity': 5,
                        'purchase_rate': Decimal('75000.00'),
                        'quantity': 5,
                    }
                ]
            },
            {
                'name': 'HP Pavilion 15',
                'category': 'Laptops',
                'selling_price': '55000.00',
                'minimum_stock': 5,
                'maximum_stock': 30,
                'purchases': [
                    {
                        'supplier': 'HP India',
                        'quantity': 8,
                        'purchase_rate': Decimal('42000.00'),
                    }
                ]
            },
            {
                'name': 'Lenovo ThinkPad E14',
                'category': 'Laptops',
                'selling_price': '65000.00',
                'minimum_stock': 4,
                'maximum_stock': 25,
                'purchases': [
                    {
                        'supplier': 'Lenovo India',
                        'quantity': 6,
                        'purchase_rate': Decimal('50000.00'),
                    }
                ]
            },
            {
                'name': 'Dell OptiPlex 7090',
                'category': 'Desktops',
                'selling_price': '85000.00',
                'minimum_stock': 2,
                'maximum_stock': 15,
                'purchases': [
                    {
                        'supplier': 'Dell India',
                        'quantity': 3,
                        'purchase_rate': Decimal('65000.00'),
                    }
                ]
            },
            {
                'name': 'Gaming Desktop Setup',
                'category': 'Desktops',
                'selling_price': '150000.00',
                'minimum_stock': 1,
                'maximum_stock': 10,
                'purchases': [
                    {
                        'supplier': 'ASUS India',
                        'quantity': 2,
                        'purchase_rate': Decimal('115000.00'),
                    }
                ]
            },
            {
                'name': 'Dell Monitor 24"',
                'category': 'Peripherals',
                'selling_price': '18000.00',
                'minimum_stock': 10,
                'maximum_stock': 50,
                'purchases': [
                    {
                        'supplier': 'Dell India',
                        'quantity': 20,
                        'purchase_rate': Decimal('12000.00'),
                    }
                ]
            },
            {
                'name': 'Mechanical Keyboard',
                'category': 'Peripherals',
                'selling_price': '8000.00',
                'minimum_stock': 15,
                'maximum_stock': 100,
                'purchases': [
                    {
                        'supplier': 'ASUS India',
                        'quantity': 30,
                        'purchase_rate': Decimal('5000.00'),
                    }
                ]
            },
            {
                'name': 'Gaming Mouse',
                'category': 'Peripherals',
                'selling_price': '5000.00',
                'minimum_stock': 20,
                'maximum_stock': 150,
                'purchases': [
                    {
                        'supplier': 'ASUS India',
                        'quantity': 50,
                        'purchase_rate': Decimal('3000.00'),
                    }
                ]
            },
            {
                'name': 'SSD 1TB NVMe',
                'category': 'Components',
                'selling_price': '12000.00',
                'minimum_stock': 10,
                'maximum_stock': 80,
                'purchases': [
                    {
                        'supplier': 'HP India',
                        'quantity': 25,
                        'purchase_rate': Decimal('8000.00'),
                    }
                ]
            },
            {
                'name': 'RAM 16GB DDR4',
                'category': 'Components',
                'selling_price': '6000.00',
                'minimum_stock': 15,
                'maximum_stock': 100,
                'purchases': [
                    {
                        'supplier': 'Kingston',
                        'quantity': 40,
                        'purchase_rate': Decimal('4000.00'),
                    }
                ]
            },
        ]

        # Get or create first user for audit trail
        user = User.objects.first() or User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin'
        )

        for item_data in items_data:
            purchases_data = item_data.pop('purchases', [])
            item_data['category'] = categories[item_data['category']]
            item_data['selling_price'] = Decimal(str(item_data['selling_price']))

            item, created = Item.objects.get_or_create(
                name=item_data['name'],
                category=item_data['category'],
                defaults=item_data
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created item: {item.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'→ Item already exists: {item.name}')
                )

            # Create purchases
            for purchase_data in purchases_data:
                supplier_name = purchase_data.pop('supplier')
                supplier = suppliers.get(supplier_name)
                if not supplier:
                    continue

                purchase_rate = Decimal(str(purchase_data['purchase_rate']))
                quantity = purchase_data['quantity']

                purchase, created = Purchase.objects.get_or_create(
                    item=item,
                    supplier=supplier,
                    purchase_date=timezone.now().date(),
                    defaults={
                        'quantity': quantity,
                        'purchase_rate': purchase_rate,
                        'total_purchase_price': quantity * purchase_rate,
                        'selling_price': item.selling_price,
                        'created_by': user
                    }
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ Purchase: {quantity} units of {item.name} '
                            f'from {supplier.name}'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                '\n✓ Sample data initialized successfully!\n'
                'Access the inventory module at: http://localhost:8000/inventory/'
            )
        )
