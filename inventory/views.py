"""Views for Inventory Management."""

from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Prefetch
from django.db.models import Q, Sum, F, Count, DecimalField
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from inventory.models import (
    Item,
    Category,
    Supplier,
    Purchase,
    SaleReceipt,
    SaleReceiptLine,
    Inventory,
    StockMovement,
    LowStockAlert,
)
from inventory.forms import (
    ItemForm,
    CategoryForm,
    InventoryEntryForm,
    SupplierForm,
    PurchaseForm,
    PurchaseHistoryFilterForm,
    SaleReceiptForm,
    SaleReceiptLineFormSet,
)
from inventory.services import (
    build_item_insight_payload,
    create_inventory_entry,
    create_sales_receipt,
    record_stock_movement,
)


# ==================== DASHBOARD ====================


@login_required
def inventory_dashboard(request):
    total_items = Item.objects.filter(is_active=True).count()
    low_stock_items = Item.objects.filter(
        is_active=True, current_stock__lte=F("minimum_stock")
    ).count()
    overstocked_items = Item.objects.filter(
        is_active=True, current_stock__gt=F("maximum_stock")
    ).count()

    # Calculate today's revenue and receipts
    today = timezone.localdate()
    today_sales = SaleReceipt.objects.filter(sale_date=today).aggregate(
        revenue=Sum("grand_total"), count=Count("id")
    )
    today_revenue = today_sales["revenue"] or Decimal("0.00")
    today_receipts = today_sales["count"] or 0

    # Calculate this month's revenue and receipts
    month_sales = SaleReceipt.objects.filter(
        sale_date__year=today.year, sale_date__month=today.month
    ).aggregate(revenue=Sum("grand_total"), count=Count("id"))
    month_revenue = month_sales["revenue"] or Decimal("0.00")
    month_receipts = month_sales["count"] or 0

    # Calculate customers this month (unique phone numbers from this month's receipts)
    customer_count = SaleReceipt.objects.filter(
        sale_date__year=today.year, sale_date__month=today.month
    ).values("customer_phone").distinct().count()

    # Get recent sales
    recent_sales = SaleReceipt.objects.prefetch_related("lines").order_by("-sale_date", "-created_at")[:5]

    # Get top selling items this month
    top_items = (
        SaleReceiptLine.objects.filter(
            receipt__sale_date__year=today.year,
            receipt__sale_date__month=today.month
        )
        .values("item__name")
        .annotate(
            total_qty=Sum("quantity"),
            total_revenue=Sum("line_total")
        )
        .order_by("-total_qty")[:5]
    )

    # 7-day revenue trend
    from datetime import timedelta
    chart_labels = []
    chart_data = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_sales = SaleReceipt.objects.filter(sale_date=day).aggregate(
            day_total=Sum("grand_total")
        )
        chart_labels.append(day.strftime("%a"))
        chart_data.append(float(day_sales["day_total"] or 0))

    context = {
        "page_title": "Inventory & Sales Dashboard",
        "total_items": total_items,
        "total_categories": Category.objects.filter(is_active=True).count(),
        "total_suppliers": Supplier.objects.filter(is_active=True).count(),
        "total_purchases": Purchase.objects.count(),
        "total_sales_receipts": SaleReceipt.objects.count(),
        "low_stock_items": low_stock_items,
        "overstocked_items": overstocked_items,
        "healthy_stock_items": max(total_items - low_stock_items - overstocked_items, 0),
        "healthy_stock_pct": int((max(total_items - low_stock_items - overstocked_items, 0) / total_items) * 100) if total_items else 0,
        "low_stock_pct": int((low_stock_items / total_items) * 100) if total_items else 0,
        "overstocked_pct": int((overstocked_items / total_items) * 100) if total_items else 0,
        "active_page": "inventory",
        "today_revenue": today_revenue,
        "today_receipts": today_receipts,
        "month_revenue": month_revenue,
        "month_receipts": month_receipts,
        "customer_count": customer_count,
        "recent_sales": recent_sales,
        "top_items": top_items,
        "chart_labels": chart_labels,
        "chart_data": chart_data,
    }

    # Calculate inventory value
    items_with_value = Item.objects.filter(is_active=True).aggregate(
        total_value=Sum(
            F("current_stock") * F("average_purchase_rate"),
            output_field=DecimalField(),
        ),
        total_selling_value=Sum(
            F("current_stock") * F("selling_price"),
            output_field=DecimalField(),
        ),
        total_profit=Sum(
            F("current_stock") * (F("selling_price") - F("average_purchase_rate")),
            output_field=DecimalField(),
        ),
    )

    context.update({
        "total_inventory_value": items_with_value["total_value"] or Decimal("0.00"),
        "total_selling_value": items_with_value["total_selling_value"]
        or Decimal("0.00"),
        "total_potential_profit": items_with_value["total_profit"]
        or Decimal("0.00"),
    })

    # Recent purchases
    context["recent_purchases"] = Purchase.objects.select_related(
        "item", "supplier"
    ).order_by("-purchase_date")[:10]
    context["recent_items"] = Item.objects.filter(is_active=True).select_related(
        "category"
    ).order_by("-updated_at")[:6]

    # Low stock alerts
    context["low_stock_alerts"] = LowStockAlert.objects.filter(
        status__in=["active", "acknowledged"]
    ).select_related("item").order_by("-created_at")[:5]

    return render(request, "inventory/dashboard.html", context)


# ==================== ITEM MANAGEMENT ====================


@login_required
def add_item(request):
    """Add a new inventory item."""
    if request.method == "POST":
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save()
            messages.success(request, f"Item '{item.name}' added successfully!")
            return redirect("inventory:item-detail", pk=item.pk)
        for error in form.errors.values():
            messages.error(request, error)
    else:
        form = ItemForm(
            initial={
                "minimum_stock": 5,
                "maximum_stock": 100,
                "gst_percentage": Decimal("18.00"),
            }
        )

    context = {
        "form": form,
        "page_title": "Add New Item",
        "active_page": "inventory_add_item",
    }
    return render(request, "inventory/add_item_form.html", context)


@login_required
def search_item_autocomplete(request):
    """API endpoint for item search autocomplete"""
    query = request.GET.get("q", "").strip()
    category_id = request.GET.get("category_id")

    if len(query) < 2:
        return JsonResponse({"results": []})

    items = Item.objects.filter(
        Q(name__icontains=query) | Q(sku__icontains=query),
        is_active=True,
    )

    if category_id:
        items = items.filter(category_id=category_id)

    items = items.values(
        "id", "name", "sku", "category__name", "current_stock",
        "average_purchase_rate", "latest_purchase_rate", "selling_price"
    )[:15]

    results = []
    for item in items:
        results.append({
            "id": item["id"],
            "text": f"{item['name']} ({item['sku']})",
            "name": item["name"],
            "sku": item["sku"],
            "category": item["category__name"],
            "stock": item["current_stock"],
            "avg_rate": float(item["average_purchase_rate"]),
            "latest_rate": float(item["latest_purchase_rate"]),
            "selling_price": float(item["selling_price"]),
        })

    return JsonResponse({"results": results})


@login_required
def item_insights_api(request, pk):
    """Return item purchase and stock insights for the unified entry page."""
    item = get_object_or_404(
        Item.objects.select_related("category"),
        pk=pk,
        is_active=True,
    )
    return JsonResponse({"success": True, "item": build_item_insight_payload(item)})


@login_required
def item_detail(request, pk):
    """View item details and purchase history"""
    item = get_object_or_404(Item, pk=pk, is_active=True)
    purchases = item.purchases.select_related("supplier").order_by("-purchase_date")

    # Pagination
    paginator = Paginator(purchases, 20)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    context = {
        "item": item,
        "page_obj": page_obj,
        "total_purchases": purchases.count(),
        "page_title": f"Item: {item.name}",
        "active_page": "inventory",
    }

    return render(request, "inventory/item_detail.html", context)


class ItemListView(LoginRequiredMixin, ListView):
    """List all items"""
    model = Item
    template_name = "inventory/item_list.html"
    context_object_name = "items"
    paginate_by = 20

    def get_queryset(self):
        queryset = Item.objects.filter(is_active=True).select_related(
            "category"
        )

        # Filter by category
        category_id = self.request.GET.get("category")
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # Filter by low stock
        low_stock = self.request.GET.get("low_stock")
        if low_stock == "true":
            queryset = queryset.filter(current_stock__lte=F("minimum_stock"))

        # Filter by overstocked
        overstocked = self.request.GET.get("overstocked")
        if overstocked == "true":
            queryset = queryset.filter(current_stock__gt=F("maximum_stock"))

        # Search
        search_query = self.request.GET.get("search")
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | Q(sku__icontains=search_query)
            )

        # Sorting
        sort_by = self.request.GET.get("sort_by", "-created_at")
        if sort_by in ["name", "-name", "current_stock", "-current_stock",
                       "selling_price", "-selling_price", "-created_at"]:
            queryset = queryset.order_by(sort_by)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.filter(is_active=True)
        context["page_title"] = "Items"
        context["active_page"] = "inventory_items"
        return context


@login_required
def edit_item(request, pk):
    """Edit item details"""
    item = get_object_or_404(Item, pk=pk, is_active=True)

    if request.method == "POST":
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f"Item '{item.name}' updated successfully!")
            return redirect("inventory:item-detail", pk=item.pk)
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = ItemForm(instance=item)

    context = {
        "form": form,
        "item": item,
        "page_title": f"Edit Item: {item.name}",
    }
    return render(request, "inventory/edit_item.html", context)


@login_required
@require_POST
def delete_item(request, pk):
    """Delete item (soft delete by marking inactive)"""
    item = get_object_or_404(Item, pk=pk)
    item_name = item.name
    item.is_active = False
    item.save()
    messages.success(request, f"Item '{item_name}' deleted successfully!")
    return redirect("inventory:item-list")


# ==================== CATEGORY MANAGEMENT ====================


class CategoryListView(LoginRequiredMixin, ListView):
    """List all categories"""
    model = Category
    template_name = "inventory/category_list.html"
    context_object_name = "categories"
    paginate_by = 20

    def get_queryset(self):
        return Category.objects.filter(is_active=True).annotate(
            item_count=Count("items")
        ).order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Categories"
        context["active_page"] = "inventory_categories"
        return context


@login_required
def add_category(request):
    """Add new category"""
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, "Category added successfully!")
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                # Return JSON for AJAX requests
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Category added",
                        "category": {
                            "id": category.pk,
                            "name": category.name,
                        },
                    }
                )
            return redirect("inventory:category-list")
        else:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({
                    "success": False,
                    "errors": form.errors,
                })
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = CategoryForm()

    context = {"form": form, "page_title": "Add Category", "active_page": "inventory_categories"}
    return render(request, "inventory/add_category.html", context)


@login_required
@require_POST
def category_quick_create_api(request):
    """AJAX endpoint for quick category creation from the unified entry page."""
    form = CategoryForm(request.POST)
    if form.is_valid():
        category = form.save()
        return JsonResponse(
            {
                "success": True,
                "category": {
                    "id": category.pk,
                    "name": category.name,
                },
            }
        )
    return JsonResponse({"success": False, "errors": form.errors}, status=400)


@login_required
def edit_category(request, pk):
    """Edit category"""
    category = get_object_or_404(Category, pk=pk, is_active=True)

    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f"Category '{category.name}' updated!")
            return redirect("inventory:category-list")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = CategoryForm(instance=category)

    context = {
        "form": form,
        "category": category,
        "page_title": f"Edit Category: {category.name}",
        "active_page": "inventory_categories",
    }
    return render(request, "inventory/edit_category.html", context)


@login_required
@require_POST
def delete_category(request, pk):
    """Delete category (soft delete)"""
    category = get_object_or_404(Category, pk=pk)

    # Check if category has active items
    if category.items.filter(is_active=True).exists():
        messages.error(
            request,
            f"Cannot delete category '{category.name}' - it has active items!",
        )
        return redirect("inventory:category-list")

    category_name = category.name
    category.is_active = False
    category.save()
    messages.success(request, f"Category '{category_name}' deleted!")
    return redirect("inventory:category-list")


# ==================== SUPPLIER MANAGEMENT ====================


class SupplierListView(LoginRequiredMixin, ListView):
    """List all suppliers"""
    model = Supplier
    template_name = "inventory/supplier_list.html"
    context_object_name = "suppliers"
    paginate_by = 20

    def get_queryset(self):
        queryset = Supplier.objects.filter(is_active=True)

        search_query = self.request.GET.get("search")
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query)
                | Q(email__icontains=search_query)
                | Q(phone__icontains=search_query)
            )

        return queryset.order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Suppliers"
        context["active_page"] = "inventory_suppliers"
        return context


@login_required
def add_supplier(request):
    """Add new supplier"""
    if request.method == "POST":
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            messages.success(request, "Supplier added successfully!")
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "supplier": {
                            "id": supplier.pk,
                            "name": supplier.name,
                        },
                    }
                )
            return redirect("inventory:supplier-list")
        else:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "errors": form.errors}, status=400)
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = SupplierForm()

    context = {"form": form, "page_title": "Add Supplier", "active_page": "inventory_suppliers"}
    return render(request, "inventory/add_supplier.html", context)


@login_required
@require_POST
def supplier_quick_create_api(request):
    """AJAX endpoint for quick supplier creation from the unified entry page."""
    form = SupplierForm(request.POST)
    if form.is_valid():
        supplier = form.save()
        return JsonResponse(
            {
                "success": True,
                "supplier": {
                    "id": supplier.pk,
                    "name": supplier.name,
                },
            }
        )
    return JsonResponse({"success": False, "errors": form.errors}, status=400)


@login_required
def edit_supplier(request, pk):
    """Edit supplier details"""
    supplier = get_object_or_404(Supplier, pk=pk, is_active=True)

    if request.method == "POST":
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, f"Supplier '{supplier.name}' updated!")
            return redirect("inventory:supplier-list")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = SupplierForm(instance=supplier)

    context = {
        "form": form,
        "supplier": supplier,
        "page_title": f"Edit Supplier: {supplier.name}",
        "active_page": "inventory_suppliers",
    }
    return render(request, "inventory/edit_supplier.html", context)


@login_required
def supplier_detail(request, pk):
    """View supplier details and purchase history"""
    supplier = get_object_or_404(Supplier, pk=pk, is_active=True)
    purchases = supplier.purchases.select_related("item").order_by(
        "-purchase_date"
    )

    # Calculate stats
    total_purchases = purchases.count()
    total_spent = purchases.aggregate(
        total=Sum("total_purchase_price", default=Decimal("0.00"))
    )["total"]

    # Pagination
    paginator = Paginator(purchases, 20)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    context = {
        "supplier": supplier,
        "page_obj": page_obj,
        "total_purchases": total_purchases,
        "total_spent": total_spent,
        "page_title": f"Supplier: {supplier.name}",
        "active_page": "inventory_suppliers",
    }

    return render(request, "inventory/supplier_detail.html", context)


# ==================== PURCHASE MANAGEMENT ====================


@login_required
def add_stock(request):
    """Add stock for an existing inventory item."""
    if request.method == "POST":
        form = PurchaseForm(request.POST)
        if form.is_valid():
            try:
                purchase = form.save(commit=False)
                purchase.created_by = request.user
                purchase.save()
                Inventory.objects.get_or_create(item=purchase.item)
                record_stock_movement(
                    item=purchase.item,
                    movement_type="purchase",
                    quantity=purchase.quantity,
                    user=request.user,
                    reference=str(purchase.pk),
                    notes=f"Purchase recorded at {purchase.purchase_rate} per unit.",
                )

                messages.success(
                    request,
                    f"Stock added for '{purchase.item.name}': {purchase.quantity} units recorded.",
                )
                return redirect("inventory:item-detail", pk=purchase.item.pk)
            except Exception as e:
                messages.error(request, f"Error saving purchase: {str(e)}")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        initial = {
            "purchase_date": timezone.localdate(),
            "quantity": 1,
        }
        item_id = request.GET.get("item_id")
        if item_id and Item.objects.filter(pk=item_id, is_active=True).exists():
            initial["item"] = item_id
        form = PurchaseForm(initial=initial)

    context = {
        "form": form,
        "page_title": "Add Stock / Record Purchase",
        "active_page": "inventory_add_stock",
    }
    return render(request, "inventory/add_purchase.html", context)


@login_required
def add_purchase(request):
    """Backward-compatible purchase entry route."""
    return add_stock(request)


# ==================== SALES MANAGEMENT ====================


@login_required
def add_sale(request):
    """Record a customer sale and generate a receipt."""
    if request.method == "POST":
        form = SaleReceiptForm(request.POST)
        formset = SaleReceiptLineFormSet(request.POST, prefix="lines")
        if form.is_valid() and formset.is_valid():
            try:
                receipt = create_sales_receipt(form, formset, request.user)
                messages.success(request, f"Sale recorded successfully. Receipt {receipt.receipt_no} is ready.")
                return redirect("inventory:sale-receipt-detail", pk=receipt.pk)
            except Exception as exc:
                form.add_error(None, f"Unable to record sale: {exc}")
        else:
            messages.error(request, "Please correct the highlighted sale fields and try again.")
    else:
        form = SaleReceiptForm(initial={"sale_date": timezone.localdate(), "payment_mode": "Cash"})
        formset = SaleReceiptLineFormSet(prefix="lines")

    context = {
        "form": form,
        "formset": formset,
        "page_title": "Record Sale",
        "active_page": "inventory_sales",
        "sale_items": list(
            Item.objects.filter(is_active=True)
            .select_related("category")
            .values("id", "name", "category__name", "current_stock", "selling_price", "gst_percentage")
        ),
    }
    return render(request, "inventory/add_sale.html", context)


@login_required
def sale_receipt_detail(request, pk):
    """Show printable customer sale receipt."""
    receipt = get_object_or_404(
        SaleReceipt.objects.prefetch_related("lines__item"),
        pk=pk,
    )
    context = {
        "receipt": receipt,
        "page_title": f"Receipt {receipt.receipt_no}",
        "active_page": "inventory_sales",
    }
    return render(request, "inventory/sale_receipt_detail.html", context)


class SaleReceiptListView(LoginRequiredMixin, ListView):
    """List customer sales receipts with filtering and reprint actions."""

    model = SaleReceipt
    template_name = "inventory/sale_history.html"
    context_object_name = "receipts"
    paginate_by = 20

    def get_queryset(self):
        queryset = SaleReceipt.objects.prefetch_related(
            Prefetch("lines", queryset=SaleReceiptLine.objects.select_related("item"))
        ).order_by("-sale_date", "-created_at")

        search_query = self.request.GET.get("search", "").strip()
        if search_query:
            queryset = queryset.filter(
                Q(receipt_no__icontains=search_query)
                | Q(customer_name__icontains=search_query)
                | Q(customer_phone__icontains=search_query)
                | Q(lines__item__name__icontains=search_query)
            ).distinct()

        payment_mode = self.request.GET.get("payment_mode")
        if payment_mode:
            queryset = queryset.filter(payment_mode=payment_mode)

        start_date = self.request.GET.get("start_date")
        if start_date:
            queryset = queryset.filter(sale_date__gte=start_date)

        end_date = self.request.GET.get("end_date")
        if end_date:
            queryset = queryset.filter(sale_date__lte=end_date)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filtered_queryset = self.get_queryset()
        context["page_title"] = "Sales History"
        context["active_page"] = "inventory_sales_history"
        context["payment_modes"] = ["Cash", "UPI", "Card", "Bank Transfer"]
        context["sales_totals"] = filtered_queryset.aggregate(
            total_receipts=Count("id"),
            total_sales=Sum("grand_total", default=Decimal("0.00")),
            total_gst=Sum("gst_amount", default=Decimal("0.00")),
        )
        return context


class PurchaseListView(LoginRequiredMixin, ListView):
    """List all purchases with filtering"""
    model = Purchase
    template_name = "inventory/purchase_list.html"
    context_object_name = "purchases"
    paginate_by = 30

    def get_queryset(self):
        queryset = Purchase.objects.select_related("item", "supplier").order_by(
            "-purchase_date"
        )

        # Apply filters
        item_id = self.request.GET.get("item")
        if item_id:
            queryset = queryset.filter(item_id=item_id)

        supplier_id = self.request.GET.get("supplier")
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)

        start_date = self.request.GET.get("start_date")
        if start_date:
            queryset = queryset.filter(purchase_date__gte=start_date)

        end_date = self.request.GET.get("end_date")
        if end_date:
            queryset = queryset.filter(purchase_date__lte=end_date)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["items"] = Item.objects.filter(is_active=True)
        context["suppliers"] = Supplier.objects.filter(is_active=True)
        context["page_title"] = "Purchase History"
        context["filter_form"] = PurchaseHistoryFilterForm(self.request.GET)
        return context


@login_required
def edit_purchase(request, pk):
    """Edit purchase record"""
    purchase = get_object_or_404(Purchase, pk=pk)

    if request.method == "POST":
        form = PurchaseForm(request.POST, instance=purchase)
        if form.is_valid():
            purchase = form.save(commit=False)
            purchase.updated_by = request.user
            purchase.save()

            messages.success(request, "Purchase updated successfully!")
            return redirect("inventory:item-detail", pk=purchase.item.pk)
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = PurchaseForm(instance=purchase)

    context = {
        "form": form,
        "purchase": purchase,
        "page_title": "Edit Purchase",
    }
    return render(request, "inventory/edit_purchase.html", context)


@login_required
@require_POST
def delete_purchase(request, pk):
    """Delete purchase record"""
    purchase = get_object_or_404(Purchase, pk=pk)
    item = purchase.item
    purchase.delete()
    messages.success(request, "Purchase deleted successfully!")
    return redirect("inventory:item-detail", pk=item.pk)


# ==================== REPORTS ====================


@login_required
def inventory_report(request):
    """Generate inventory report"""
    items = Item.objects.filter(is_active=True).select_related("category")

    # Filter by category
    category_id = request.GET.get("category")
    if category_id:
        items = items.filter(category_id=category_id)

    # Calculate totals
    totals = items.aggregate(
        total_items=Count("id"),
        total_quantity=Sum("current_stock", default=0),
        total_value=Sum(
            F("current_stock") * F("average_purchase_rate"),
            output_field=DecimalField(),
        ),
        total_selling_value=Sum(
            F("current_stock") * F("selling_price"),
            output_field=DecimalField(),
        ),
        total_profit=Sum(
            F("current_stock") * (F("selling_price") - F("average_purchase_rate")),
            output_field=DecimalField(),
        ),
    )

    context = {
        "items": items,
        "categories": Category.objects.filter(is_active=True),
        "totals": totals,
        "page_title": "Inventory Report",
    }

    return render(request, "inventory/inventory_report.html", context)


@login_required
def category_report(request):
    """Generate category-wise report"""
    categories = Category.objects.filter(is_active=True).annotate(
        item_count=Count("items"),
        total_quantity=Sum("items__current_stock"),
        total_value=Sum(
            F("items__current_stock") * F("items__average_purchase_rate"),
            output_field=DecimalField(),
        ),
    ).order_by("-total_value")

    context = {
        "categories": categories,
        "page_title": "Category Report",
    }

    return render(request, "inventory/category_report.html", context)


@login_required
def supplier_report(request):
    """Generate supplier report"""
    suppliers = Supplier.objects.filter(is_active=True).annotate(
        purchase_count=Count("purchases"),
        total_spent=Sum("purchases__total_purchase_price", default=Decimal("0.00")),
    ).order_by("-total_spent")

    context = {
        "suppliers": suppliers,
        "page_title": "Supplier Report",
    }

    return render(request, "inventory/supplier_report.html", context)


# ==================== LOW STOCK ALERTS ====================


@login_required
def low_stock_alerts(request):
    """View low stock alerts"""
    status = request.GET.get("status", "active")
    alerts = LowStockAlert.objects.select_related("item").filter(
        status=status
    ).order_by("-created_at")

    if request.GET.get("resolve") and request.method == "POST":
        alert_id = request.POST.get("alert_id")
        alert = get_object_or_404(LowStockAlert, pk=alert_id)
        alert.status = "resolved"
        alert.resolved_at = timezone.now()
        alert.save()
        messages.success(request, "Alert marked as resolved!")
        return redirect("inventory:low-stock-alerts")

    context = {
        "alerts": alerts,
        "status": status,
        "page_title": "Low Stock Alerts",
    }

    return render(request, "inventory/low_stock_alerts.html", context)
