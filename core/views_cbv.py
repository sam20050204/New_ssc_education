"""
Class-Based Views (CBV) refactoring guide for Django best practices.

This file demonstrates how to migrate function-based views (FBV) to Class-Based Views (CBV)
for better code organization, reusability, and maintainability.

CBV Benefits:
- Better code organization and reusability through inheritance
- Built-in mixins for common patterns (LoginRequiredMixin, PaginationMixin)
- Cleaner URL routing using as_view()
- Better separation of HTTP methods (get, post)
"""

from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView,
    TemplateView, View, FormView
)
from django.views.generic.edit import FormMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Q, Sum, Count
from decimal import Decimal
import json
from datetime import timedelta
from django.utils import timezone

from .models import Enquiry, AdmittedStudent, FeePayment, Course, Student
from .forms import EnquiryForm, AdmittedStudentForm, FeePaymentForm, CourseForm


# ==================== HOME PAGE ====================

class HomePageView(FormView):
    """
    Home page with enquiry form submission.
    
    Replaces: home() FBV
    
    Key Features:
    - Inherits from FormView for automatic form handling
    - Handles GET requests showing form
    - Handles POST requests with form validation
    - Prevents duplicate enquiries within 5 minutes
    """
    template_name = 'core/home.html'
    form_class = EnquiryForm
    success_url = reverse_lazy('home')
    
    def get_context_data(self, **kwargs):
        """Add courses to context for form rendering."""
        context = super().get_context_data(**kwargs)
        context['all_courses'] = Course.objects.all().order_by('name')
        return context
    
    def form_valid(self, form):
        """Handle valid form submission with duplicate check."""
        # Check for duplicate enquiry (within last 5 minutes)
        five_minutes_ago = timezone.now() - timedelta(minutes=5)
        duplicate = Enquiry.objects.filter(
            name__iexact=form.cleaned_data['name'],
            mobile=form.cleaned_data['mobile'],
            created_at__gte=five_minutes_ago
        ).exists()
        
        if duplicate:
            messages.warning(self.request, "⚠️ Similar enquiry already submitted recently!")
        else:
            form.save()
            messages.success(self.request, "✅ Enquiry submitted successfully!")
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Handle form validation errors."""
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"❌ {field}: {error}")
        return super().form_invalid(form)


# ==================== ENQUIRY MANAGEMENT ====================

class EnquiryListView(LoginRequiredMixin, ListView):
    """
    List all enquiries with pagination and filtering.
    
    Replaces: enquiry_list() FBV
    
    Key Features:
    - Automatic pagination (default 20 items per page)
    - Automatic queryset handling
    - Template context automatically includes 'enquiry_list' variable
    - LoginRequiredMixin ensures only logged-in users access
    """
    model = Enquiry
    template_name = 'core/enquiry_list.html'
    context_object_name = 'enquiries'
    paginate_by = 20
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter enquiries based on search and filters."""
        queryset = Enquiry.objects.all().order_by('-created_at')
        
        # Search functionality
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(mobile__icontains=search) |
                Q(course__icontains=search) |
                Q(city__icontains=search)
            )
        
        # Date range filtering
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Add filter values to context."""
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['total_count'] = Enquiry.objects.count()
        context['today_count'] = Enquiry.objects.filter(
            created_at__date=timezone.now().date()
        ).count()
        return context


class EnquiryDetailView(LoginRequiredMixin, DetailView):
    """
    Display single enquiry details.
    
    Replaces: enquiry_detail() FBV
    
    Key Features:
    - Automatic object lookup by primary key from URL kwargs
    - Automatic context variable (object or custom context_object_name)
    - 404 automatically raised if object not found
    """
    model = Enquiry
    template_name = 'core/enquiry_detail.html'
    context_object_name = 'enquiry'
    pk_url_kwarg = 'id'  # Use 'id' instead of 'pk' from URL


class EnquiryDeleteView(LoginRequiredMixin, DeleteView):
    """
    Delete an enquiry.
    
    Replaces: delete_enquiry() FBV
    
    Key Features:
    - Automatic GET → confirmation template
    - Automatic POST → deletion
    - Automatic redirect after deletion
    """
    model = Enquiry
    template_name = 'core/enquiry_confirm_delete.html'
    success_url = reverse_lazy('enquiry_list')
    pk_url_kwarg = 'id'
    
    def delete(self, request, *args, **kwargs):
        """Add success message on deletion."""
        enquiry_name = self.get_object().name
        messages.success(request, f"✅ Enquiry for {enquiry_name} has been deleted!")
        return super().delete(request, *args, **kwargs)


# ==================== ADMISSION MANAGEMENT ====================

class AdmissionCreateView(LoginRequiredMixin, CreateView):
    """
    Create new student admission.
    
    Replaces: new_admission() FBV
    
    Key Features:
    - Automatic model form handling from CreateView
    - Automatic redirect after successful creation
    - Automatic context setup
    - File upload handling built-in
    """
    model = AdmittedStudent
    form_class = AdmittedStudentForm
    template_name = 'core/new_admission.html'
    success_url = reverse_lazy('new_admission')
    
    def get_context_data(self, **kwargs):
        """Add courses to context."""
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'new_admission'
        context['all_courses'] = Course.objects.all().order_by('name')
        context['enquiry_data'] = self.request.session.get('enquiry_conversion', {})
        return context
    
    def form_valid(self, form):
        """Handle successful form submission."""
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"✅ Admission for {self.object.full_name} successfully recorded! Total Fees: ₹{self.object.total_fees}"
        )
        return response
    
    def form_invalid(self, form):
        """Handle form validation errors."""
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"❌ {field}: {error}")
        return super().form_invalid(form)


class AdmissionListView(LoginRequiredMixin, ListView):
    """
    List all admitted students with filtering and search.
    
    Replaces: admitted_students() FBV
    
    Key Features:
    - Pagination support
    - Dynamic filtering by course, month, year, city
    - Full-text search capability
    """
    model = AdmittedStudent
    template_name = 'core/admitted_students.html'
    context_object_name = 'students'
    paginate_by = 25
    ordering = ['-admission_date']
    
    def get_queryset(self):
        """Filter students based on search and multiple criteria."""
        queryset = AdmittedStudent.objects.all().order_by('-admission_date')
        
        # Search by name, mobile, course
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(mobile_own__icontains=search) |
                Q(course__icontains=search)
            )
        
        # Filter by course
        course = self.request.GET.get('course', '')
        if course:
            queryset = queryset.filter(course=course)
        
        # Filter by month/year (batch)
        month = self.request.GET.get('month', '')
        year = self.request.GET.get('year', '')
        if month:
            queryset = queryset.filter(batch_month=month)
        if year:
            queryset = queryset.filter(batch_year=year)
        
        # Filter by city
        city = self.request.GET.get('city', '')
        if city:
            queryset = queryset.filter(city=city)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Add filter options and statistics to context."""
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'admitted_students'
        context['all_courses'] = Course.objects.all().order_by('name')
        context['total_students'] = AdmittedStudent.objects.count()
        context['total_revenue'] = AdmittedStudent.objects.aggregate(
            total=Sum('total_fees')
        )['total'] or 0
        context['total_fees_collected'] = AdmittedStudent.objects.aggregate(
            total=Sum('paid_fees')
        )['total'] or 0
        
        # Add filter values to context for form preservation
        context['search'] = self.request.GET.get('search', '')
        context['selected_course'] = self.request.GET.get('course', '')
        context['selected_month'] = self.request.GET.get('month', '')
        context['selected_year'] = self.request.GET.get('year', '')
        context['selected_city'] = self.request.GET.get('city', '')
        
        return context


class AdmissionDetailView(LoginRequiredMixin, DetailView):
    """
    Display detailed student admission record.
    
    Replaces: student_detail_admitted() FBV
    
    Key Features:
    - Automatic object retrieval and context setup
    - Related data accessible in template
    """
    model = AdmittedStudent
    template_name = 'core/student_detail_admitted.html'
    context_object_name = 'student'
    pk_url_kwarg = 'student_id'
    
    def get_context_data(self, **kwargs):
        """Add related data to context."""
        context = super().get_context_data(**kwargs)
        student = self.object
        
        # Get all fee payments for this student
        context['payments'] = FeePayment.objects.filter(
            student=student
        ).order_by('-payment_date')
        
        # Calculate statistics
        context['total_paid'] = FeePayment.objects.filter(
            student=student
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        context['remaining_fees'] = max(0, student.total_fees - student.paid_fees)
        
        return context


class AdmissionUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update student admission details.
    
    Replaces: update_student_admitted() FBV
    
    Key Features:
    - Automatic form population with existing data
    - Built-in file upload handling
    - Easy success message integration
    """
    model = AdmittedStudent
    form_class = AdmittedStudentForm
    template_name = 'core/update_student_admitted.html'
    pk_url_kwarg = 'student_id'
    
    def get_success_url(self):
        """Redirect back to student detail page."""
        return reverse_lazy('student_detail_admitted', kwargs={'student_id': self.object.id})
    
    def form_valid(self, form):
        """Add success message on update."""
        messages.success(
            self.request,
            f"✅ Student details for {self.object.full_name} updated successfully!"
        )
        return super().form_valid(form)


class AdmissionDeleteView(LoginRequiredMixin, DeleteView):
    """
    Delete admitted student record.
    
    Replaces: delete_admitted_students() FBV
    
    Key Features:
    - Confirmation template support
    - Automatic cascade delete handling
    """
    model = AdmittedStudent
    template_name = 'core/admitted_student_confirm_delete.html'
    success_url = reverse_lazy('admitted_students')
    
    def delete(self, request, *args, **kwargs):
        """Add success message."""
        student_name = self.get_object().full_name
        messages.success(request, f"✅ Student record for {student_name} deleted!")
        return super().delete(request, *args, **kwargs)


# ==================== FEE MANAGEMENT ====================

class FeePaymentView(LoginRequiredMixin, TemplateView):
    """
    Fee payment page with AJAX student search.
    
    Replaces: fees_payment() FBV (GET) + submit_fee_payment() (POST via AJAX)
    
    Key Features:
    - Inherits from TemplateView for static page rendering
    - No database queries by default
    - AJAX endpoints can be handled separately
    """
    template_name = 'core/fees_payment.html'
    
    def get_context_data(self, **kwargs):
        """Add payment modes to context."""
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'fees_payment'
        context['payment_modes'] = [
            ('Cash', 'Cash'),
            ('Cheque', 'Cheque'),
            ('Online', 'Online Transfer'),
            ('NEFT', 'NEFT'),
            ('Other', 'Other'),
        ]
        return context


class StudentSearchAPIView(LoginRequiredMixin, View):
    """
    AJAX endpoint for searching students by name/mobile.
    
    Replaces: search_students_for_payment() FBV
    
    Key Features:
    - Inherits from View for raw HTTP method handling
    - Returns JSON response
    - No template required
    """
    def get(self, request, *args, **kwargs):
        """Search students by query string."""
        query = request.GET.get('q', '').strip()
        
        if len(query) < 2:
            return JsonResponse({'students': []})
        
        students = AdmittedStudent.objects.filter(
            Q(full_name__icontains=query) |
            Q(student_name__icontains=query) |
            Q(mobile_own__icontains=query)
        ).order_by('full_name')[:10]
        
        students_data = [
            {
                'id': student.id,
                'full_name': student.full_name,
                'mobile_own': student.mobile_own,
                'course': (student.custom_course if student.course == 'Other' 
                          and student.custom_course else student.course)
            }
            for student in students
        ]
        
        return JsonResponse({'students': students_data})


# ==================== MIGRATION GUIDE ====================

"""
HOW TO MIGRATE YOUR VIEWS TO CBV:

1. FORMS-BASED VIEWS (Create, Update, Delete):
   Old: def new_admission(request): ... form processing ...
   New: class AdmissionCreateView(LoginRequiredMixin, CreateView):
   
   Benefits:
   - Automatic form population
   - Automatic CSRF protection
   - Built-in file upload handling
   - Easy success URL routing

2. LIST VIEWS (Display multiple objects):
   Old: def admitted_students(request): ... queryset filtering ...
   New: class AdmissionListView(LoginRequiredMixin, ListView):
   
   Benefits:
   - Automatic pagination
   - Built-in ordering
   - Cleaner get_queryset() method
   - Context automatically populated

3. DETAIL VIEWS (Display single object):
   Old: def student_detail_admitted(request, student_id):
           student = get_object_or_404(...)
   New: class AdmissionDetailView(LoginRequiredMixin, DetailView):
   
   Benefits:
   - Automatic 404 handling
   - Automatic context setup
   - Related object access simplified

4. DELETE VIEWS (With confirmation):
   Old: def delete_enquiry(request, id):
           if request.method == 'POST': ... delete ...
   New: class EnquiryDeleteView(LoginRequiredMixin, DeleteView):
   
   Benefits:
   - Automatic confirmation template
   - Automatic deletion handling
   - Built-in success message support

5. GENERIC VIEWS (Page rendering):
   Old: def home(request): return render(...)
   New: class HomePageView(TemplateView): pass
   
   Benefits:
   - Cleaner code
   - Easy context addition via get_context_data()
   - Automatic template resolution

6. CUSTOM API VIEWS (JSON responses):
   Old: def search_students_for_payment(request):
           return JsonResponse(...)
   New: class StudentSearchAPIView(LoginRequiredMixin, View):
           def get(self, request, ...):
   
   Benefits:
   - Explicit HTTP method handling
   - Mixins for authentication/permissions
   - Better code organization

URL ROUTING CHANGES:

Old (FBV):
    path('enquiry/', views.enquiry_list, name='enquiry_list'),
    path('enquiry/<int:id>/', views.enquiry_detail, name='enquiry_detail'),

New (CBV):
    path('enquiry/', views.EnquiryListView.as_view(), name='enquiry_list'),
    path('enquiry/<int:id>/', views.EnquiryDetailView.as_view(), name='enquiry_detail'),

COMMON MIXINS:

1. LoginRequiredMixin
   - Redirects unauthenticated users to login
   - Usage: class MyView(LoginRequiredMixin, ListView): pass

2. PaginationMixin (built into ListView/DetailView)
   - Automatic pagination
   - Usage: paginate_by = 20

3. UserPassesTestMixin
   - Custom permission checking
   - Usage: def test_func(self): return self.request.user.is_staff

4. MultipleObjectMixin
   - Multiple object handling
   - Usage: pagination_number = 50

KEY ATTRIBUTES:

- model: Required for generic views (Enquiry, Student, etc.)
- template_name: Template path (auto-generated if not specified)
- context_object_name: Variable name in template (default: 'object' or 'object_list')
- paginate_by: Items per page (20, 50, 100)
- ordering: Default queryset ordering (['-created_at'])
- form_class: Form to use (EnquiryForm, AdmittedStudentForm)
- success_url: Redirect after successful operation
- pk_url_kwarg: URL parameter for object ID (default: 'pk')

BEST PRACTICES:

✅ Override get_queryset() for filtering/search
✅ Override get_context_data() to add extra context
✅ Use get_success_url() for dynamic redirects
✅ Use get_object_or_404() in get_object() for custom logic
✅ Add messages in form_valid()/delete() for user feedback
✅ Use LoginRequiredMixin for authentication

❌ Avoid putting business logic in __init__()
❌ Avoid modifying self.request.user data
❌ Avoid hardcoded URLs (use reverse_lazy())
❌ Avoid complex template logic (move to view)

PERFORMANCE TIPS:

1. Use select_related() for ForeignKey/OneToOne
2. Use prefetch_related() for reverse relations
3. Add db_index=True to frequently filtered fields
4. Use only() / defer() to limit field selection
5. Use cache_page() decorator for expensive queries

TESTING CBV:

from django.test import TestCase
from django.contrib.auth.models import User

class EnquiryListViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test', password='test123')
        self.client.login(username='test', password='test123')
    
    def test_list_view_GET(self):
        response = self.client.get('/enquiry/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/enquiry_list.html')
    
    def test_list_view_pagination(self):
        response = self.client.get('/enquiry/?page=2')
        self.assertEqual(response.status_code, 200)
    
    def test_list_view_search(self):
        response = self.client.get('/enquiry/?search=test')
        self.assertEqual(response.status_code, 200)
"""
