"""Customer management views for Inventory/Sales module."""

from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from inventory.models import Customer


class CustomerListView(LoginRequiredMixin, ListView):
    """List all customers with search and purchase stats."""
    model = Customer
    template_name = "inventory/customer_list.html"
    context_object_name = "customers"
    paginate_by = 25

    def get_queryset(self):
        qs = Customer.objects.filter(is_active=True).annotate(
            total_purchases=Count("sales_receipts"),
            total_spent=Sum("sales_receipts__grand_total", default=Decimal("0.00")),
        )
        q = self.request.GET.get("search", "").strip()
        if q:
            qs = qs.filter(
                Q(name__icontains=q) | Q(phone__icontains=q) | Q(email__icontains=q)
            )
        return qs.order_by("name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Customers"
        ctx["active_page"] = "inventory_customers"
        ctx["total_customers"] = Customer.objects.filter(is_active=True).count()
        return ctx


@login_required
def customer_detail(request, pk):
    """Customer detail with full purchase history."""
    customer = get_object_or_404(Customer, pk=pk, is_active=True)
    receipts = customer.sales_receipts.prefetch_related(
        "lines__item"
    ).order_by("-sale_date", "-created_at")
    paginator = Paginator(receipts, 15)
    page_obj = paginator.get_page(request.GET.get("page", 1))
    context = {
        "customer": customer,
        "page_obj": page_obj,
        "total_receipts": receipts.count(),
        "total_spent": customer.get_total_spent(),
        "page_title": f"Customer: {customer.name}",
        "active_page": "inventory_customers",
    }
    return render(request, "inventory/customer_detail.html", context)


@login_required
def add_customer(request):
    """Add a new customer record."""
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        phone = request.POST.get("phone", "").strip()
        email = request.POST.get("email", "").strip()
        address = request.POST.get("address", "").strip()
        city = request.POST.get("city", "").strip()
        notes = request.POST.get("notes", "").strip()
        if not name:
            messages.error(request, "Customer name is required.")
        else:
            customer = Customer.objects.create(
                name=name, phone=phone, email=email,
                address=address, city=city, notes=notes,
            )
            messages.success(request, f"Customer '{customer.name}' added successfully!")
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({
                    "success": True,
                    "customer": {"id": customer.pk, "name": str(customer)}
                })
            return redirect("inventory:customer-detail", pk=customer.pk)
    context = {"page_title": "Add Customer", "active_page": "inventory_customers"}
    return render(request, "inventory/add_customer.html", context)


@login_required
def edit_customer(request, pk):
    """Edit customer details."""
    customer = get_object_or_404(Customer, pk=pk, is_active=True)
    if request.method == "POST":
        customer.name = request.POST.get("name", customer.name).strip()
        customer.phone = request.POST.get("phone", "").strip()
        customer.email = request.POST.get("email", "").strip()
        customer.address = request.POST.get("address", "").strip()
        customer.city = request.POST.get("city", "").strip()
        customer.notes = request.POST.get("notes", "").strip()
        if not customer.name:
            messages.error(request, "Customer name is required.")
        else:
            customer.save()
            messages.success(request, f"Customer '{customer.name}' updated!")
            return redirect("inventory:customer-detail", pk=customer.pk)
    context = {
        "customer": customer,
        "page_title": f"Edit Customer: {customer.name}",
        "active_page": "inventory_customers",
    }
    return render(request, "inventory/edit_customer.html", context)


@login_required
@require_POST
def delete_customer(request, pk):
    """Soft-delete a customer."""
    customer = get_object_or_404(Customer, pk=pk)
    customer.is_active = False
    customer.save()
    messages.success(request, f"Customer '{customer.name}' removed.")
    return redirect("inventory:customer-list")


@login_required
def customer_search_api(request):
    """AJAX autocomplete — customer name/phone search."""
    q = request.GET.get("q", "").strip()
    if len(q) < 2:
        return JsonResponse({"results": []})
    customers = Customer.objects.filter(
        Q(name__icontains=q) | Q(phone__icontains=q),
        is_active=True,
    ).values("id", "name", "phone", "address", "city")[:10]
    return JsonResponse({"results": list(customers)})
