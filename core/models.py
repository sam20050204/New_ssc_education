from django.db import models, transaction
from django.core.validators import MinValueValidator
from decimal import Decimal
from datetime import date
from core.validators import validate_image_file

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
    COURSE_CHOICES = [
        ('MS-CIT', 'MS-CIT'),
        ('Tally', 'Tally'),
        ('Advance Excel', 'Advance Excel'),
        ('IOT', 'IOT'),
        ('Scratch', 'Scratch'),
        ('Other', 'Other'),
    ]
    
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    
    MARITAL_STATUS_CHOICES = [
        ('Single', 'Single'),
        ('Married', 'Married'),
    ]
    
    course = models.CharField(max_length=50, choices=COURSE_CHOICES)
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
        default=5000
    )
    paid_fees = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        default=0
    )
    
    admission_date = models.DateField(default=date.today, help_text="Date of admission")
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.full_name
    
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
    PAYMENT_MODE_CHOICES = [
        ('Cash', 'Cash'),
        ('UPI', 'UPI'),
        ('Card', 'Card'),
        ('Bank Transfer', 'Bank Transfer'),
    ]
    
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
        if not self.receipt_no:
            with transaction.atomic():
                last_payment = FeePayment.objects.select_for_update().order_by('-id').first()
                if last_payment and last_payment.receipt_no:
                    last_number = int(last_payment.receipt_no.split('-')[1])
                    new_number = last_number + 1
                else:
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
        return mkcl_1 + mkcl_2
    
    @property
    def profit(self):
        """Calculate profit (Total Paid - MKCL Fees)"""
        total_paid = self.student.paid_fees or 0
        return total_paid - self.total_mkcl_fees


class Attendance(models.Model):
    """Daily attendance records for admitted students"""
    STATUS_CHOICES = [
        ('P', 'Present'),
        ('A', 'Absent'),
    ]

    student = models.ForeignKey(
        'AdmittedStudent',
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    date = models.DateField(db_index=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    remarks = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendance Records'
        unique_together = ('student', 'date')
        ordering = ['-date', 'student']

    def __str__(self):
        return f"{self.student.full_name} - {self.date} - {self.get_status_display()}"


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


class StudentTimetable(models.Model):
    """Student timetable for theory and practical sessions"""
    
    SESSION_TYPE_CHOICES = [
        ('Theory', 'Theory'),
        ('Practical', 'Practical'),
    ]
    
    TIME_SLOT_CHOICES = [
        ('09:00-10:00', '09:00 - 10:00 AM'),
        ('10:00-11:00', '10:00 - 11:00 AM'),
        ('11:00-12:00', '11:00 - 12:00 PM'),
        ('12:00-13:00', '12:00 - 1:00 PM'),
        ('13:00-14:00', '1:00 - 2:00 PM'),
        ('14:00-15:00', '2:00 - 3:00 PM'),
        ('15:00-16:00', '3:00 - 4:00 PM'),
        ('16:00-17:00', '4:00 - 5:00 PM'),
        ('17:00-18:00', '5:00 - 6:00 PM'),
    ]
    
    DAYS_OF_WEEK = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]
    
    # Foreign Keys
    student = models.ForeignKey(
        AdmittedStudent,
        on_delete=models.CASCADE,
        related_name='timetable_slots'
    )
    
    # Timetable Fields
    day = models.CharField(
        max_length=10,
        choices=DAYS_OF_WEEK,
        help_text="Day of the week"
    )
    
    time_slot = models.CharField(
        max_length=11,
        choices=TIME_SLOT_CHOICES,
        help_text="Time slot for the session (1 hour each)"
    )
    
    session_type = models.CharField(
        max_length=20,
        choices=SESSION_TYPE_CHOICES,
        default='Theory',
        help_text="Type of session - Theory or Practical"
    )
    
    batch_month = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        db_index=True,
        help_text="Batch month for filtering"
    )
    
    batch_year = models.CharField(
        max_length=4,
        blank=True,
        null=True,
        db_index=True,
        help_text="Batch year for filtering"
    )
    
    course = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        db_index=True,
        help_text="Course name for filtering"
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes for this slot"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['day', 'time_slot']
        verbose_name = 'Student Timetable'
        verbose_name_plural = 'Student Timetables'
        unique_together = ['student', 'day', 'time_slot']
        indexes = [
            models.Index(fields=['student']),
            models.Index(fields=['day', 'time_slot']),
            models.Index(fields=['batch_month', 'batch_year']),
            models.Index(fields=['course']),
        ]
    
    def __str__(self):
        return f"{self.student.full_name} - {self.day} {self.time_slot} ({self.session_type})"
    
    @property
    def day_time_display(self):
        """Return formatted day and time"""
        return f"{self.day}, {self.get_time_slot_display()}"
