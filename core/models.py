from django.db import models, transaction
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date
from core.validators import validate_image_file
from core.constants import (
    COURSE_CHOICES, GENDER_CHOICES, MARITAL_STATUS_CHOICES,
    TIME_SLOT_CHOICES, PAYMENT_MODE_CHOICES, ATTENDANCE_STATUS_CHOICES,
    BATCH_TYPE_CHOICES, DEFAULT_TOTAL_FEES
)

class Enquiry(models.Model):
    """Lead enquiries for prospective students"""
    name = models.CharField(max_length=100, db_index=True)
    mobile = models.CharField(max_length=15)
    education = models.CharField(max_length=100)
    course = models.CharField(max_length=50)
    custom_course = models.CharField(max_length=100, blank=True, null=True)
    
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    taluka = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Enquiry'
        verbose_name_plural = 'Enquiries'
        indexes = [
            models.Index(fields=['mobile']),
            models.Index(fields=['course']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return self.name
    
    def get_display_course(self):
        """Return the display course name"""
        if self.course == 'Other' and self.custom_course:
            return self.custom_course
        return self.course

    
class AdmittedStudent(models.Model):
    COURSE_CHOICES = COURSE_CHOICES
    GENDER_CHOICES = GENDER_CHOICES
    MARITAL_STATUS_CHOICES = MARITAL_STATUS_CHOICES
    
    # Note: course field has NO choices constraint here to allow dynamic courses from database
    # Validation is handled in AdmittedStudentForm.__init__
    course = models.CharField(max_length=50)
    custom_course = models.CharField(max_length=100, blank=True, null=True, help_text="If 'Other' is selected")
    
    student_name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    mother_name = models.CharField(max_length=100, blank=True, null=True)
    full_name = models.CharField(max_length=300)
    date_of_birth = models.DateField()
    
    mobile_own = models.CharField(max_length=15)
    parent_mobile = models.CharField(max_length=15, blank=True, null=True)
    
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    marital_status = models.CharField(max_length=10, choices=MARITAL_STATUS_CHOICES)
    
    address = models.TextField()
    city = models.CharField(max_length=100)
    tehsil_block = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    pin_code = models.CharField(max_length=10)
    
    educational_qualification = models.CharField(max_length=200)

    batch_month = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        help_text="Month of batch (e.g., January, February)"
    )
    batch_year = models.CharField(
        max_length=4, 
        blank=True, 
        null=True,
        help_text="Year of batch (e.g., 2024, 2025)"
    )
    
    # Timetable & Attendance Management Fields
    theory_batch_time = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=TIME_SLOT_CHOICES,
        help_text="Fixed daily theory batch timing"
    )
    practical_batch_time = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=TIME_SLOT_CHOICES,
        help_text="Fixed daily practical batch timing"
    )

    @property
    def batch_display(self):
        """Return formatted batch string"""
        if self.batch_month and self.batch_year:
            return f"{self.batch_month} {self.batch_year}"
        return "Not Assigned"
    
    photo = models.ImageField(
        upload_to='student_photos/',
        blank=True,
        null=True,
        validators=[validate_image_file],
        help_text="Upload student photo (JPG, PNG, GIF, max 5MB)"
    )
    
    total_fees = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        default=DEFAULT_TOTAL_FEES
    )
    paid_fees = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        default=0
    )
    
    admission_date = models.DateField(default=date.today, help_text="Date of admission")
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def formatted_full_name(self):
        parts = [self.surname, self.student_name, self.father_name]
        return " ".join(part.strip() for part in parts if part and part.strip())

    def save(self, *args, **kwargs):
        self.full_name = self.formatted_full_name
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.formatted_full_name
    
    @property
    def remaining_fees(self):
        return (self.total_fees or Decimal('0')) - (self.paid_fees or Decimal('0'))
    
    @property
    def fees_percentage_paid(self):
        if self.total_fees and self.total_fees > 0:
            return (self.paid_fees / self.total_fees) * Decimal('100')
        return Decimal('0')
    
    class Meta:
        ordering = ['-admission_date']
        verbose_name = 'Admitted Student'
        verbose_name_plural = 'Admitted Students'
        indexes = [
            models.Index(fields=['course']),
            models.Index(fields=['admission_date']),
            models.Index(fields=['mobile_own']),
            models.Index(fields=['-admission_date']),
        ]


class Course(models.Model):
    """Course offered by the institution"""
    name = models.CharField(max_length=100, unique=True, db_index=True)
    duration = models.CharField(max_length=50, help_text="e.g., 3 months, 6 weeks")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
    
    def __str__(self):
        return f"{self.name} ({self.duration})"


class Student(models.Model):
    """Student enrollment records"""
    name = models.CharField(max_length=200, db_index=True)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True, unique=True)
    photo = models.ImageField(
        upload_to='student_photos/',
        blank=True,
        null=True,
        validators=[validate_image_file],
        help_text="Upload student photo (JPG, PNG, GIF, max 5MB)"
    )
    
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        related_name='enrolled_students',
        help_text="Select enrolled course"
    )
    admission_date = models.DateField(default=date.today, db_index=True)
    
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    
    parent_name = models.CharField(max_length=200, blank=True, null=True)
    parent_phone = models.CharField(max_length=15, blank=True, null=True)
    
    total_fees = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    paid_fees = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    
    qualification = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    
    is_active = models.BooleanField(default=True, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-admission_date', 'name']
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        indexes = [
            models.Index(fields=['course', 'admission_date']),
            models.Index(fields=['is_active']),
            models.Index(fields=['phone']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.course.name if self.course else 'No Course'}"
    
    @property
    def remaining_fees(self):
        """Calculate remaining fees"""
        return self.total_fees - self.paid_fees
    
    @property
    def fees_percentage_paid(self):
        """Calculate percentage of fees paid"""
        if self.total_fees > 0:
            return (self.paid_fees / self.total_fees) * 100
        return 0


class FeePayment(models.Model):
    PAYMENT_MODE_CHOICES = PAYMENT_MODE_CHOICES
    
    receipt_no = models.CharField(max_length=20, unique=True, editable=False)
    
    student = models.ForeignKey(
        'AdmittedStudent', 
        on_delete=models.CASCADE,
        related_name='fee_payments'
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES)
    payment_date = models.DateField(default=date.today, help_text="Date of payment")
    
    remarks = models.TextField(blank=True, null=True)
    
    total_fees_at_payment = models.DecimalField(max_digits=10, decimal_places=2)
    paid_before_this = models.DecimalField(max_digits=10, decimal_places=2)
    remaining_after_this = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-payment_date']
        verbose_name = 'Fee Payment'
        verbose_name_plural = 'Fee Payments'
        indexes = [
            models.Index(fields=['student', 'payment_date']),
            models.Index(fields=['payment_date']),
            models.Index(fields=['receipt_no']),
        ]
    
    def __str__(self):
        return f"{self.receipt_no} - {self.student.full_name} - Rs. {self.amount}"
    
    def save(self, *args, **kwargs):
        # Prevent modification of receipt number after creation
        if self.pk:
            # This is an update - fetch the original receipt_no and restore it
            original = FeePayment.objects.get(pk=self.pk)
            if self.receipt_no != original.receipt_no:
                self.receipt_no = original.receipt_no
        
        if not self.receipt_no:
            # This is a new record - generate sequential receipt number
            with transaction.atomic():
                # Get the last receipt and extract the number
                # Find the last receipt with proper RCP prefix (ignore TEMP prefixes)
                last_payment = FeePayment.objects.select_for_update().filter(
                    receipt_no__startswith='RCP-'
                ).order_by('-created_at').first()
                
                if last_payment and last_payment.receipt_no:
                    try:
                        # Extract number from receipt_no (e.g., "RCP-000091" -> 91)
                        last_number = int(last_payment.receipt_no.split('-')[-1])
                        new_number = last_number + 1
                    except (ValueError, IndexError):
                        # Fallback if parsing fails
                        new_number = int(FeePayment.objects.filter(receipt_no__startswith='RCP-').count()) + 1
                else:
                    # If no RCP- receipts exist, start from 1
                    new_number = 1
                self.receipt_no = f"RCP-{new_number:06d}"
        super().save(*args, **kwargs)


class StudentFinanceDetail(models.Model):
    """Detailed financial information for admitted students"""
    student = models.OneToOneField(
        'AdmittedStudent',
        on_delete=models.CASCADE,
        related_name='finance_detail',
        help_text="Student associated with this finance record"
    )
    first_installment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        blank=True,
        null=True
    )
    second_installment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        blank=True,
        null=True
    )
    third_installment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        blank=True,
        null=True
    )
    fourth_installment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        blank=True,
        null=True
    )
    fifth_installment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        blank=True,
        null=True
    )
    fees_paid_to_mkcl_1 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        blank=True,
        null=True
    )
    fees_paid_to_mkcl_2 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        blank=True,
        null=True
    )
    fees_paid_to_mkcl_3 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Student Finance Detail'
        verbose_name_plural = 'Student Finance Details'
    
    def __str__(self):
        return f"Finance Detail - {self.student.full_name}"
    
    @property
    def total_mkcl_fees(self):
        """Calculate total fees paid to MKCL"""
        mkcl_1 = self.fees_paid_to_mkcl_1 or 0
        mkcl_2 = self.fees_paid_to_mkcl_2 or 0
        mkcl_3 = self.fees_paid_to_mkcl_3 or 0
        return mkcl_1 + mkcl_2 + mkcl_3
    
    @property
    def profit(self):
        """Calculate profit (Total Paid - MKCL Fees)"""
        total_paid = self.student.paid_fees or 0
        return total_paid - self.total_mkcl_fees


class Attendance(models.Model):
    """Daily attendance records for admitted students with theory and practical tracking"""
    STATUS_CHOICES = ATTENDANCE_STATUS_CHOICES

    student = models.ForeignKey(
        'AdmittedStudent',
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    date = models.DateField(db_index=True)
    
    # Original field (kept for backward compatibility)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A', blank=True, null=True)
    
    # New fields for theory and practical attendance
    theory_attendance = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        default='A',
        help_text="Theory session attendance"
    )
    practical_attendance = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        default='A',
        help_text="Practical session attendance"
    )
    
    remarks = models.CharField(max_length=255, blank=True, null=True)
    marked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marked_attendances'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendance Records'
        unique_together = ('student', 'date')
        ordering = ['-date', 'student']
        indexes = [
            models.Index(fields=['student', 'date']),
            models.Index(fields=['date']),
        ]

    def __str__(self):
        theory_status = self.get_theory_attendance_display()
        practical_status = self.get_practical_attendance_display()
        return f"{self.student.full_name} - {self.date} - Theory: {theory_status} / Practical: {practical_status}"
    
    def get_theory_attendance_display(self):
        """Get display name for theory attendance"""
        if not self.theory_attendance:
            return 'Not Taken'
        for value, display in self.STATUS_CHOICES:
            if value == self.theory_attendance:
                return display
        return 'Absent'
    
    def get_practical_attendance_display(self):
        """Get display name for practical attendance"""
        if not self.practical_attendance:
            return 'Not Taken'
        for value, display in self.STATUS_CHOICES:
            if value == self.practical_attendance:
                return display
        return 'Absent'


class SalesItem(models.Model):
    """Inventory management for sales items"""
    item_name = models.CharField(max_length=200, db_index=True)
    quantity = models.PositiveIntegerField(help_text="Quantity in stock")
    purchase_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Purchase rate per unit"
    )
    purchased_from = models.CharField(max_length=200, help_text="Vendor/supplier name")
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Total purchase amount"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Sales Item'
        verbose_name_plural = 'Sales Items'
        indexes = [
            models.Index(fields=['item_name']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.item_name} (Qty: {self.quantity})"
    
    @property
    def calculated_total(self):
        """Calculate total amount based on quantity and purchase rate"""
        return self.quantity * self.purchase_rate


class Batch(models.Model):
    """Predefined batch timings for theory and practical sessions"""
    BATCH_TIME_CHOICES = TIME_SLOT_CHOICES
    
    batch_type = models.CharField(
        max_length=20, 
        choices=BATCH_TYPE_CHOICES,
        help_text="Type of batch session"
    )
    time_slot = models.CharField(
        max_length=20,
        choices=BATCH_TIME_CHOICES,
        db_index=True,
        help_text="Time slot for the batch"
    )
    course = models.ForeignKey(
        'Course',
        on_delete=models.CASCADE,
        related_name='batches',
        null=True,
        blank=True,
        help_text="Course this batch belongs to (optional for common batches)"
    )
    capacity = models.PositiveIntegerField(
        default=50,
        help_text="Maximum students in this batch"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Batch'
        verbose_name_plural = 'Batches'
        unique_together = ('batch_type', 'time_slot', 'course')
        ordering = ['batch_type', 'time_slot']
        indexes = [
            models.Index(fields=['batch_type', 'time_slot']),
        ]
    
    def __str__(self):
        return f"{self.batch_type} - {self.get_time_slot_display()} - {self.course or 'All Courses'}"
    
    def get_time_slot_display(self):
        """Return formatted time slot"""
        for value, display in self.BATCH_TIME_CHOICES:
            if value == self.time_slot:
                return display
        return self.time_slot
    
    @property
    def current_strength(self):
        """Get current number of students in this batch"""
        if self.batch_type == 'Theory':
            filters = {'theory_batch_time': self.time_slot}
        else:
            filters = {'practical_batch_time': self.time_slot}
        
        # Only filter by course if this batch is course-specific
        if self.course is not None:
            filters['course'] = self.course
        
        return AdmittedStudent.objects.filter(**filters).count()

