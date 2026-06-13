"""
URL Configuration for Inventory Management
"""

from django.urls import path
from inventory import views
from inventory import customer_views

app_name = "inventory"

urlpatterns = [
    # Dashboard
    path("", views.inventory_dashboard, name="dashboard"),

    # Items
    path("items/", views.ItemListView.as_view(), name="item-list"),
    path("items/add/", views.add_item, name="add-item"),
    path("items/<int:pk>/", views.item_detail, name="item-detail"),
    path("items/<int:pk>/edit/", views.edit_item, name="edit-item"),
    path("items/<int:pk>/delete/", views.delete_item, name="delete-item"),

    # Categories
    path("categories/", views.CategoryListView.as_view(), name="category-list"),
    path("categories/add/", views.add_category, name="add-category"),
    path("categories/<int:pk>/edit/", views.edit_category, name="edit-category"),
    path("categories/<int:pk>/delete/", views.delete_category, name="delete-category"),

    # Suppliers
    path("suppliers/", views.SupplierListView.as_view(), name="supplier-list"),
    path("suppliers/add/", views.add_supplier, name="add-supplier"),
    path("suppliers/<int:pk>/", views.supplier_detail, name="supplier-detail"),
    path("suppliers/<int:pk>/edit/", views.edit_supplier, name="edit-supplier"),

    # Purchases / Stock
    path("stock/add/", views.add_stock, name="add-stock"),
    path("sales/add/", views.add_sale, name="add-sale"),
    path("sales/history/", views.SaleReceiptListView.as_view(), name="sale-history"),
    path("sales/receipts/<int:pk>/", views.sale_receipt_detail, name="sale-receipt-detail"),
    path("purchases/", views.PurchaseListView.as_view(), name="purchase-list"),
    path("purchases/add/", views.add_purchase, name="add-purchase"),
    path("purchases/<int:pk>/edit/", views.edit_purchase, name="edit-purchase"),
    path("purchases/<int:pk>/delete/", views.delete_purchase, name="delete-purchase"),

    # Reports
    path("reports/inventory/", views.inventory_report, name="inventory-report"),
    path("reports/category/", views.category_report, name="category-report"),
    path("reports/supplier/", views.supplier_report, name="supplier-report"),

    # Alerts
    path("alerts/low-stock/", views.low_stock_alerts, name="low-stock-alerts"),

    # Customers
    path("customers/", customer_views.CustomerListView.as_view(), name="customer-list"),
    path("customers/add/", customer_views.add_customer, name="add-customer"),
    path("customers/<int:pk>/", customer_views.customer_detail, name="customer-detail"),
    path("customers/<int:pk>/edit/", customer_views.edit_customer, name="edit-customer"),
    path("customers/<int:pk>/delete/", customer_views.delete_customer, name="delete-customer"),

    # API
    path("api/items/search/", views.search_item_autocomplete, name="item-search-api"),
    path("api/items/<int:pk>/insights/", views.item_insights_api, name="item-insights-api"),
    path("api/categories/create/", views.category_quick_create_api, name="category-quick-create-api"),
    path("api/suppliers/create/", views.supplier_quick_create_api, name="supplier-quick-create-api"),
    path("api/customers/search/", customer_views.customer_search_api, name="customer-search-api"),
]
