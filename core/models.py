from django.db import models

class Enquiry(models.Model):
    name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15)
    education = models.CharField(max_length=100)
    course = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


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
    
    # Photo
    photo = models.ImageField(upload_to='student_photos/', blank=True, null=True)
    
    # Metadata
    admission_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.full_name
    
    class Meta:
        ordering = ['-admission_date']
        verbose_name = 'Admitted Student'
        verbose_name_plural = 'Admitted Students'