"""
Forms for Inventory Management
"""

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from decimal import Decimal

from inventory.models import (
    Item,
    Category,
    Supplier,
    Purchase,
    Inventory,
)
from inventory.services import get_or_create_category_by_name


def _bootstrap_control(attrs=None, **extra):
    merged = {"class": "form-control"}
    if attrs:
        merged.update(attrs)
    merged.update(extra)
    return merged


class CategoryForm(forms.ModelForm):
    """Form for adding and editing categories"""

    class Meta:
        model = Category
        fields = ["name", "description", "icon"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "E.g., Laptops, Desktops, Peripherals",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Category description",
                    "rows": 3,
                }
            ),
            "icon": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "E.g., fa-laptop, fa-desktop",
                    "data-toggle": "popover",
                    "data-content": "Font Awesome icon class (https://fontawesome.com)",
                }
            ),
        }

    def clean_name(self):
        """Validate category name"""
        name = self.cleaned_data.get("name", "").strip()
        if not name:
            raise ValidationError("Category name cannot be empty.")

        # Check for duplicates (case-insensitive)
        existing = Category.objects.filter(
            name__iexact=name
        ).exclude(pk=self.instance.pk if self.instance.pk else None)

        if existing.exists():
            raise ValidationError(
                f"Category '{name}' already exists. Please use a different name."
            )

        return name


class SupplierForm(forms.ModelForm):
    """Form for adding and editing suppliers"""

    class Meta:
        model = Supplier
        fields = [
            "name",
            "contact_person",
            "email",
            "phone",
            "alternate_phone",
            "address",
            "city",
            "state",
            "pincode",
            "gst_number",
            "payment_terms",
            "website",
            "notes",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Supplier name"}
            ),
            "contact_person": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Contact person name"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "Email address"}
            ),
            "phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Phone number"}
            ),
            "alternate_phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Alternate phone"}
            ),
            "address": forms.Textarea(
                attrs={"class": "form-control", "placeholder": "Full address", "rows": 3}
            ),
            "city": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "City"}
            ),
            "state": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "State"}
            ),
            "pincode": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Pincode"}
            ),
            "gst_number": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "GST Number"}
            ),
            "payment_terms": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "E.g., Net 30, COD"}
            ),
            "website": forms.URLInput(
                attrs={"class": "form-control", "placeholder": "Website URL"}
            ),
            "notes": forms.Textarea(
                attrs={"class": "form-control", "placeholder": "Additional notes", "rows": 3}
            ),
        }

    def clean_name(self):
        """Validate supplier name"""
        name = self.cleaned_data.get("name", "").strip()
        if not name:
            raise ValidationError("Supplier name cannot be empty.")
        existing = Supplier.objects.filter(name__iexact=name).exclude(
            pk=self.instance.pk if self.instance.pk else None
        )
        if existing.exists():
            raise ValidationError(
                f"Supplier '{name}' already exists. Please use a different name."
            )
        return name


class ItemForm(forms.ModelForm):
    """Form for adding and editing items"""

    new_category = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Create new category (leave blank to use existing)",
                "id": "new_category_input",
            }
        ),
        help_text="Leave blank to select existing category",
    )

    class Meta:
        model = Item
        fields = [
            "name",
            "category",
            "sku",
            "description",
            "specifications",
            "image",
            "minimum_stock",
            "maximum_stock",
            "selling_price",
            "gst_percentage",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Item/Product name",
                    "id": "item_name_input",
                }
            ),
            "category": forms.Select(
                attrs={
                    "class": "form-control form-select",
                    "id": "category_select",
                }
            ),
            "sku": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Leave blank for auto-generation",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Item description",
                    "rows": 3,
                }
            ),
            "specifications": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Technical specifications",
                    "rows": 3,
                }
            ),
            "image": forms.FileInput(attrs={"class": "form-control"}),
            "minimum_stock": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Low stock threshold",
                    "min": "0",
                }
            ),
            "maximum_stock": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Maximum stock level",
                    "min": "1",
                }
            ),
            "selling_price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Selling price per unit",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "gst_percentage": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "GST percentage",
                    "step": "0.01",
                    "min": "0",
                    "value": "18.00",
                }
            ),
        }

    def clean(self):
        """Validate form data"""
        cleaned_data = super().clean()
        name = cleaned_data.get("name", "").strip()
        category = cleaned_data.get("category")
        new_category = cleaned_data.get("new_category", "").strip()

        if not name:
            raise ValidationError("Item name cannot be empty.")

        # Check for duplicate item in category
        if category:
            existing = Item.objects.filter(
                name__iexact=name, category=category
            ).exclude(pk=self.instance.pk if self.instance.pk else None)

            if existing.exists():
                raise ValidationError(
                    f"Item '{name}' already exists in category '{category.name}'."
                )

        if new_category and not category:
            raise ValidationError(
                "Please select or create a category for this item."
            )

        if new_category and category:
            raise ValidationError(
                "Please either select an existing category OR create a new one, not both."
            )

        return cleaned_data

    def save(self, commit=True):
        """Handle new category creation"""
        instance = super().save(commit=False)

        new_category_name = self.cleaned_data.get("new_category", "").strip()
        if new_category_name:
            instance.category = get_or_create_category_by_name(new_category_name)

        if commit:
            instance.save()
        return instance


class PurchaseForm(forms.ModelForm):
    """Form for recording purchases"""

    item_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Start typing item name or SKU...",
                "id": "item_autocomplete",
                "autocomplete": "off",
                "data-api-url": "/api/inventory/items/search/",
            }
        ),
        help_text="Search for existing item or create new",
    )

    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-control form-select",
                "id": "purchase_category_select",
            }
        ),
    )

    new_category = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Create new category",
                "id": "purchase_new_category_input",
            }
        ),
    )

    class Meta:
        model = Purchase
        fields = [
            "item",
            "supplier",
            "purchase_date",
            "quantity",
            "purchase_rate",
            "selling_price",
            "batch_number",
            "expiry_date",
            "invoice_number",
            "notes",
        ]
        widgets = {
            "item": forms.Select(
                attrs={
                    "class": "form-control form-select",
                    "id": "item_select",
                }
            ),
            "supplier": forms.Select(
                attrs={
                    "class": "form-control form-select",
                    "id": "supplier_select",
                }
            ),
            "purchase_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "quantity": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Quantity",
                    "min": "1",
                    "id": "quantity_input",
                }
            ),
            "purchase_rate": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Cost per unit",
                    "step": "0.01",
                    "min": "0",
                    "id": "purchase_rate_input",
                }
            ),
            "selling_price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Selling price per unit",
                    "step": "0.01",
                    "min": "0",
                    "id": "selling_price_input",
                }
            ),
            "batch_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Batch/Lot number",
                }
            ),
            "expiry_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "invoice_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Invoice/Bill number",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Additional notes",
                    "rows": 3,
                }
            ),
        }

    def clean(self):
        """Validate purchase form"""
        cleaned_data = super().clean()
        quantity = cleaned_data.get("quantity")
        purchase_rate = cleaned_data.get("purchase_rate")
        item = cleaned_data.get("item")

        if not item and not cleaned_data.get("item_name"):
            raise ValidationError("Please select or enter an item.")

        if quantity and quantity <= 0:
            raise ValidationError("Quantity must be greater than 0.")

        if purchase_rate is not None and purchase_rate < 0:
            raise ValidationError("Purchase rate cannot be negative.")

        return cleaned_data

    def save(self, commit=True):
        """Handle new item creation and price updates"""
        instance = super().save(commit=False)

        item_name = self.cleaned_data.get("item_name", "").strip()
        if item_name and not instance.item:
            # Find or create item
            category = self.cleaned_data.get("category")
            new_category_name = self.cleaned_data.get("new_category", "").strip()

            if new_category_name:
                category = get_or_create_category_by_name(new_category_name)

            if category:
                instance.item = Item.objects.filter(
                    name__iexact=item_name,
                    category=category,
                ).first()
                if instance.item is None:
                    instance.item = Item(
                        name=item_name,
                        category=category,
                        selling_price=self.cleaned_data.get("selling_price")
                        or Decimal("0.00"),
                    )
                    if commit:
                        instance.item.save()

        if instance.item:
            # Update item's selling price if provided
            selling_price = self.cleaned_data.get("selling_price")
            if selling_price and selling_price > 0:
                instance.item.selling_price = selling_price
                instance.item.save(update_fields=["selling_price"])

        if commit:
            instance.save()
        return instance


class InventoryEntryForm(forms.Form):
    """Unified form for item creation/update and purchase capture."""

    existing_item_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput(attrs={"id": "existing_item_id"}),
    )
    item_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs=_bootstrap_control(
                {
                    "id": "item_name_input",
                    "placeholder": "Search or type item name",
                    "autocomplete": "off",
                    "data-autocomplete-url": "/inventory/api/items/search/",
                }
            )
        ),
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        widget=forms.Select(
            attrs=_bootstrap_control(
                {
                    "class": "form-control form-select",
                    "id": "category_select",
                }
            )
        ),
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs=_bootstrap_control(
                {
                    "rows": 3,
                    "placeholder": "Short commercial description",
                }
            )
        ),
    )
    specifications = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs=_bootstrap_control(
                {
                    "rows": 4,
                    "placeholder": "Technical specifications, model details, RAM, SSD, warranty, etc.",
                }
            )
        ),
    )
    image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs=_bootstrap_control({"accept": "image/*"})),
    )
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(
            attrs=_bootstrap_control(
                {
                    "class": "form-control form-select",
                    "id": "supplier_select",
                }
            )
        ),
    )
    purchase_date = forms.DateField(
        widget=forms.DateInput(
            attrs=_bootstrap_control({"type": "date", "id": "purchase_date_input"})
        )
    )
    purchase_rate = forms.DecimalField(
        min_value=Decimal("0.00"),
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(
            attrs=_bootstrap_control(
                {
                    "id": "purchase_rate_input",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "0.00",
                }
            )
        ),
    )
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(
            attrs=_bootstrap_control(
                {
                    "id": "quantity_input",
                    "min": "1",
                    "placeholder": "1",
                }
            )
        ),
    )
    selling_price = forms.DecimalField(
        min_value=Decimal("0.00"),
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(
            attrs=_bootstrap_control(
                {
                    "id": "selling_price_input",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "0.00",
                }
            )
        ),
    )
    minimum_stock = forms.IntegerField(
        min_value=0,
        initial=5,
        widget=forms.NumberInput(
            attrs=_bootstrap_control({"id": "minimum_stock_input", "min": "0"})
        ),
    )
    maximum_stock = forms.IntegerField(
        min_value=1,
        initial=100,
        widget=forms.NumberInput(
            attrs=_bootstrap_control({"id": "maximum_stock_input", "min": "1"})
        ),
    )
    gst_percentage = forms.DecimalField(
        min_value=Decimal("0.00"),
        max_digits=5,
        decimal_places=2,
        initial=Decimal("18.00"),
        widget=forms.NumberInput(
            attrs=_bootstrap_control(
                {
                    "id": "gst_percentage_input",
                    "step": "0.01",
                    "min": "0",
                }
            )
        ),
    )
    batch_number = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(
            attrs=_bootstrap_control({"placeholder": "Optional batch / lot number"})
        ),
    )
    expiry_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs=_bootstrap_control({"type": "date"})),
    )
    invoice_number = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(
            attrs=_bootstrap_control({"placeholder": "Supplier invoice / bill number"})
        ),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs=_bootstrap_control({"rows": 3, "placeholder": "Internal notes"})
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resolved_item = None

    def clean_item_name(self):
        name = self.cleaned_data.get("item_name", "").strip()
        if not name:
            raise ValidationError("Item name is required.")
        return name

    def clean(self):
        cleaned_data = super().clean()
        item_name = cleaned_data.get("item_name", "").strip()
        category = cleaned_data.get("category")
        existing_item_id = cleaned_data.get("existing_item_id")

        if cleaned_data.get("maximum_stock") and cleaned_data.get("minimum_stock") is not None:
            if cleaned_data["maximum_stock"] <= cleaned_data["minimum_stock"]:
                self.add_error(
                    "maximum_stock",
                    "Maximum stock must be greater than minimum stock.",
                )

        resolved_item = None
        if existing_item_id:
            resolved_item = Item.objects.filter(
                pk=existing_item_id,
                is_active=True,
            ).select_related("category").first()
            if resolved_item is None:
                self.add_error("item_name", "The selected existing item is no longer available.")
        elif item_name and category:
            resolved_item = Item.objects.filter(
                name__iexact=item_name,
                category=category,
                is_active=True,
            ).select_related("category").first()

        if resolved_item is None and not category:
            self.add_error("category", "Category is required for a new item.")

        if resolved_item:
            cleaned_data["category"] = resolved_item.category

        cleaned_data["resolved_item"] = resolved_item
        self.resolved_item = resolved_item
        return cleaned_data


class PurchaseHistoryFilterForm(forms.Form):
    """Form for filtering purchase history"""

    SORT_CHOICES = [
        ("-purchase_date", "Latest First"),
        ("purchase_date", "Oldest First"),
        ("quantity", "Quantity (Low to High)"),
        ("-quantity", "Quantity (High to Low)"),
        ("purchase_rate", "Rate (Low to High)"),
        ("-purchase_rate", "Rate (High to Low)"),
    ]

    item = forms.ModelChoiceField(
        queryset=Item.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(
            attrs={"class": "form-control form-select"}
        ),
        label="Item",
    )

    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(
            attrs={"class": "form-control form-select"}
        ),
        label="Supplier",
    )

    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={"class": "form-control", "type": "date"}
        ),
        label="From Date",
    )

    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={"class": "form-control", "type": "date"}
        ),
        label="To Date",
    )

    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        widget=forms.Select(
            attrs={"class": "form-control form-select"}
        ),
        label="Sort By",
    )
