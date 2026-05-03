"""
Django Forms for SSC Education Management System

Provides proper form handling with validation instead of manual HTML processing.
"""

from django import forms
from django.core.exceptions import ValidationError
from .models import Enquiry, AdmittedStudent, FeePayment, Course
from .constants import TIME_SLOT_CHOICES, BATCH_TYPE_CHOICES
from .utils import is_valid_mobile, is_valid_pincode
import re


class EnquiryForm(forms.ModelForm):
    """Form for handling new enquiries from prospects"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically load course choices from database
        # Include both hardcoded courses and database courses
        hardcoded_courses = [
            ('MS-CIT', 'MS-CIT'),
            ('Tally', 'Tally'),
            ('Advance Excel', 'Advance Excel'),
            ('IOT', 'IOT'),
            ('Scratch', 'Scratch'),
        ]
        
        # Get courses from database
        db_courses = list(Course.objects.values_list('name', 'name').order_by('name'))
        
        # Combine and deduplicate
        all_courses = list(set(hardcoded_courses + db_courses))
        all_courses.sort(key=lambda x: x[0])
        
        # Add "Other" at the end
        all_courses.append(('Other', 'Other'))
        
        self.fields['course'].choices = all_courses
    
    class Meta:
        model = Enquiry
        fields = ['name', 'mobile', 'education', 'course', 'custom_course', 
                  'address', 'city', 'taluka', 'district']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full Name',
                'required': True
            }),
            'mobile': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '10-digit mobile number',
                'pattern': '[0-9]{10}',
                'maxlength': '10',
                'required': True
            }),
            'education': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Educational Qualification',
                'required': True
            }),
            'course': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'custom_course': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Specify course (if Other selected)'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Full Address',
                'rows': 3
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City'
            }),
            'taluka': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Taluka'
            }),
            'district': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'District'
            }),
        }
    
    def clean_mobile(self):
        """Validate mobile number"""
        mobile = self.cleaned_data.get('mobile', '').strip()
        
        if not mobile:
            raise ValidationError("Mobile number is required.")
        
        if not is_valid_mobile(mobile):
            raise ValidationError("Invalid mobile number. Must be 10 digits starting with 6, 7, 8, or 9.")
        
        return mobile
    
    def clean_name(self):
        """Validate name"""
        name = self.cleaned_data.get('name', '').strip()
        
        if not name:
            raise ValidationError("Name is required.")
        
        if len(name) < 2:
            raise ValidationError("Name must be at least 2 characters long.")
        
        if not re.match(r"^[a-zA-Z\s'-]+$", name):
            raise ValidationError("Name can only contain letters, spaces, hyphens, and apostrophes.")
        
        return name
    
    def clean_course(self):
        """Validate course - allow any course that exists in database or is a hardcoded course"""
        course = self.cleaned_data.get('course')
        
        if not course:
            raise ValidationError("Course is required.")
        
        # Hardcoded courses that are always valid
        hardcoded_courses = ['MS-CIT', 'Tally', 'Advance Excel', 'IOT', 'Scratch', 'Other']
        
        # Check if it's a hardcoded course or exists in database
        if course not in hardcoded_courses:
            # Check if it exists in the database
            if not Course.objects.filter(name__iexact=course).exists():
                raise ValidationError(f"Course '{course}' is not valid. Please add it first or select from available courses.")
        
        return course
    
    def clean(self):
        """Validate form data"""
        cleaned_data = super().clean()
        course = cleaned_data.get('course')
        custom_course = cleaned_data.get('custom_course')
        
        # Validate custom_course is provided when course is "Other"
        if course == 'Other' and not custom_course:
            raise ValidationError("Please specify a course name when 'Other' is selected.")
        
        return cleaned_data


class AdmittedStudentForm(forms.ModelForm):
    """Form for admitting new students"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically load course choices from database
        # Include both hardcoded courses and database courses
        hardcoded_courses = [
            ('MS-CIT', 'MS-CIT'),
            ('Tally', 'Tally'),
            ('Advance Excel', 'Advance Excel'),
            ('IOT', 'IOT'),
            ('Scratch', 'Scratch'),
        ]
        
        # Get courses from database
        db_courses = list(Course.objects.values_list('name', 'name').order_by('name'))
        
        # Combine and deduplicate
        all_courses = list(set(hardcoded_courses + db_courses))
        all_courses.sort(key=lambda x: x[0])
        
        # Add "Other" at the end
        all_courses.append(('Other', 'Other'))
        
        self.fields['course'].choices = all_courses
        self.fields['full_name'].required = False
    
    class Meta:
        model = AdmittedStudent
        fields = [
            'course', 'custom_course', 'student_name', 'father_name', 'surname',
            'mother_name', 'full_name', 'date_of_birth', 'mobile_own', 'parent_mobile',
            'gender', 'marital_status', 'address', 'city', 'tehsil_block',
            'district', 'pin_code', 'educational_qualification', 'batch_month',
            'batch_year', 'theory_batch_time', 'practical_batch_time', 'photo', 'total_fees'
        ]
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'custom_course': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Specify course if Other'
            }),
            'student_name': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'father_name': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'surname': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'mother_name': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'full_name': forms.HiddenInput(),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'mobile_own': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': '[0-9]{10}',
                'maxlength': '10',
                'required': True
            }),
            'parent_mobile': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': '[0-9]{10}',
                'maxlength': '10'
            }),
            'gender': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'marital_status': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'required': True
            }),
            'city': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'tehsil_block': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'district': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'pin_code': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': '[0-9]{6}',
                'maxlength': '6',
                'required': True
            }),
            'educational_qualification': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'batch_month': forms.Select(attrs={'class': 'form-control'}),
            'batch_year': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': '[0-9]{4}',
                'maxlength': '4'
            }),
            'theory_batch_time': forms.Select(attrs={'class': 'form-control'}),
            'practical_batch_time': forms.Select(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/jpeg,image/png,image/gif'
            }),
            'total_fees': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'type': 'number'
            }),
        }
    
    def clean_mobile_own(self):
        """Validate student mobile"""
        mobile = self.cleaned_data.get('mobile_own', '').strip()
        
        if not mobile:
            raise ValidationError("Student mobile number is required.")
        
        if not is_valid_mobile(mobile):
            raise ValidationError("Invalid mobile number. Must be 10 digits starting with 6, 7, 8, or 9.")
        
        return mobile
    
    def clean_pin_code(self):
        """Validate pin code"""
        pin_code = self.cleaned_data.get('pin_code', '').strip()
        
        if not pin_code:
            raise ValidationError("Pin code is required.")
        
        if not is_valid_pincode(pin_code):
            raise ValidationError("Pin code must be exactly 6 digits.")
        
        return pin_code
    
    def clean_total_fees(self):
        """Validate total fees"""
        total_fees = self.cleaned_data.get('total_fees')
        
        if total_fees is not None and total_fees < 0:
            raise ValidationError("Total fees cannot be negative.")
        
        return total_fees
    
    def clean_paid_fees(self):
        """Validate paid fees"""
        paid_fees = self.cleaned_data.get('paid_fees')
        
        if paid_fees is not None and paid_fees < 0:
            raise ValidationError("Paid fees cannot be negative.")
        
        return paid_fees
    
    def clean_course(self):
        """Validate course - allow any course that exists in database or is a hardcoded course"""
        course = self.cleaned_data.get('course')
        
        if not course:
            raise ValidationError("Course is required.")
        
        # Hardcoded courses that are always valid
        hardcoded_courses = ['MS-CIT', 'Tally', 'Advance Excel', 'IOT', 'Scratch', 'Other']
        
        # Check if it's a hardcoded course or exists in database
        if course not in hardcoded_courses:
            # Check if it exists in the database
            if not Course.objects.filter(name__iexact=course).exists():
                raise ValidationError(f"Course '{course}' is not valid. Please add it first or select from available courses.")
        
        return course
    
    def clean(self):
        """Validate form data"""
        cleaned_data = super().clean()
        course = cleaned_data.get('course')
        custom_course = cleaned_data.get('custom_course')
        total_fees = cleaned_data.get('total_fees')
        
        # Validate custom_course is provided when course is "Other"
        if course == 'Other' and not custom_course:
            raise ValidationError("Please specify a course name when 'Other' is selected.")
        
        # Validate total_fees is provided
        if not total_fees:
            raise ValidationError("Total fees must be specified.")
        
        return cleaned_data


class FeePaymentForm(forms.ModelForm):
    """Form for recording fee payments"""
    
    class Meta:
        model = FeePayment
        fields = ['student', 'amount', 'payment_mode', 'payment_date', 'remarks']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.01',
                'step': '0.01',
                'type': 'number',
                'required': True
            }),
            'payment_mode': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional remarks'
            }),
        }
    
    def clean_amount(self):
        """Validate payment amount"""
        amount = self.cleaned_data.get('amount')
        
        if amount is not None and amount <= 0:
            raise ValidationError("Payment amount must be greater than zero.")
        
        return amount


class CourseForm(forms.ModelForm):
    """Form for adding new courses"""
    
    class Meta:
        model = Course
        fields = ['name', 'duration']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Course Name',
                'required': True
            }),
            'duration': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 3 months, 6 weeks',
                'required': True
            }),
        }
    
    def clean_name(self):
        """Validate course name"""
        name = self.cleaned_data.get('name', '').strip()
        
        if not name:
            raise ValidationError("Course name is required.")
        
        if len(name) < 2:
            raise ValidationError("Course name must be at least 2 characters.")
        
        # Check if course already exists (case-insensitive)
        if Course.objects.filter(name__iexact=name).exists():
            raise ValidationError("This course already exists.")
        
        return name


class BatchManagementForm(forms.Form):
    """Form for editing student batch assignments"""
    theory_batch_time = forms.ChoiceField(
        label="Theory Batch Time",
        choices=TIME_SLOT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    practical_batch_time = forms.ChoiceField(
        label="Practical Batch Time",
        choices=TIME_SLOT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class AttendanceForm(forms.Form):
    """Form for marking attendance"""
    date = forms.DateField(
        label="Select Date",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'required': True
        })
    )
    batch_time = forms.ChoiceField(
        label="Select Batch Time",
        choices=[('', '-- Select Batch --')] + TIME_SLOT_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    batch_type = forms.ChoiceField(
        label="Select Batch Type",
        choices=[('', '-- Select Type --')] + BATCH_TYPE_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


