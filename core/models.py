from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.db import models, transaction

class Enquiry(models.Model):
    name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15)
    education = models.CharField(max_length=100)
    course = models.CharField(max_length=50)
    custom_course = models.CharField(max_length=100, blank=True, null=True)  # NEW FIELD
    
    # Address fields
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    taluka = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

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
    
    # Course Information
    course = models.CharField(max_length=50, choices=COURSE_CHOICES)
    custom_course = models.CharField(max_length=100, blank=True, null=True, help_text="If 'Other' is selected")
    
    # Personal Information
    student_name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    mother_name = models.CharField(max_length=100)
    full_name = models.CharField(max_length=300)
    date_of_birth = models.DateField()
    
    # Contact Information
    mobile_own = models.CharField(max_length=15)
    parent_mobile = models.CharField(max_length=15, blank=True, null=True)
    
    # Demographics
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    marital_status = models.CharField(max_length=10, choices=MARITAL_STATUS_CHOICES)
    
    # Address Information
    address = models.TextField()
    city = models.CharField(max_length=100)
    tehsil_block = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    pin_code = models.CharField(max_length=10)
    
    # Educational Information
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
    
    # Photo
    photo = models.ImageField(upload_to='student_photos/', blank=True, null=True)
    
    # Financial Information
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
    
    # Metadata
    admission_date = models.DateTimeField(auto_now_add=True)
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
    
    @property
    def batch_display(self):
        """Return formatted batch name"""
        if self.batch_month and self.batch_year:
            return f"{self.batch_month} {self.batch_year}"
        return "Not Assigned"
    
    class Meta:
        ordering = ['-admission_date']
        verbose_name = 'Admitted Student'
        verbose_name_plural = 'Admitted Students'


class Course(models.Model):
    name = models.CharField(max_length=100)
    duration = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name


class Student(models.Model):
    # Personal Information
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    photo = models.ImageField(upload_to='student_photos/', blank=True, null=True)
    
    # Course Information
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True)
    admission_date = models.DateField()
    
    # Address
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    
    # Parent/Guardian Information
    parent_name = models.CharField(max_length=200, blank=True, null=True)
    parent_phone = models.CharField(max_length=15, blank=True, null=True)
    
    # Financial Information
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
    
    # Additional Fields
    qualification = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['admission_date', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.course.name if self.course else 'No Course'}"
    
    @property
    def remaining_fees(self):
        return self.total_fees - self.paid_fees
    
    @property
    def fees_percentage_paid(self):
        if self.total_fees > 0:
            return (self.paid_fees / self.total_fees) * 100
        return 0


# NEW MODEL FOR FEE PAYMENTS
class FeePayment(models.Model):
    PAYMENT_MODE_CHOICES = [
        ('Cash', 'Cash'),
        ('UPI', 'UPI'),
        ('Card', 'Card'),
        ('Bank Transfer', 'Bank Transfer'),
    ]
    
    # Receipt number - auto-generated
    receipt_no = models.CharField(max_length=20, unique=True, editable=False)
    
    # Student reference
    student = models.ForeignKey(
        'AdmittedStudent', 
        on_delete=models.CASCADE,
        related_name='fee_payments'
    )
    
    # Payment details
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES)
    payment_date = models.DateTimeField(auto_now_add=True)
    
    # Additional info
    remarks = models.TextField(blank=True, null=True)
    
    # Fees snapshot at time of payment
    total_fees_at_payment = models.DecimalField(max_digits=10, decimal_places=2)
    paid_before_this = models.DecimalField(max_digits=10, decimal_places=2)
    remaining_after_this = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-payment_date']
        verbose_name = 'Fee Payment'
        verbose_name_plural = 'Fee Payments'
    
    def __str__(self):
        return f"{self.receipt_no} - {self.student.full_name} - ₹{self.amount}"
    
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
    """Model to store detailed finance information for students"""
    student = models.OneToOneField('Student', on_delete=models.CASCADE, related_name='finance_detail')
    first_installment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    second_installment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    third_installment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    fees_paid_to_mkcl_1 = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    fees_paid_to_mkcl_2 = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Student Finance Detail'
        verbose_name_plural = 'Student Finance Details'
    
    def __str__(self):
        return f"Finance Detail - {self.student.first_name} {self.student.last_name}"
    
    @property
    def total_mkcl_fees(self):
        """Calculate total fees paid to MKCL"""
        mkcl_1 = self.fees_paid_to_mkcl_1 or 0
        mkcl_2 = self.fees_paid_to_mkcl_2 or 0
        return mkcl_1 + mkcl_2
    
    @property
    def profit(self):
        """Calculate profit (Total Paid - MKCL Fees)"""
        total_paid = self.student.fees_paid or 0
        return total_paid - self.total_mkcl_fees