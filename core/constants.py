"""
Core Constants Module
Centralized definitions for choices, mappings, and configuration constants
Eliminates duplication across forms, models, and views
"""

# ==================== TIME SLOT DEFINITIONS ====================
TIME_SLOT_CHOICES = [
    ('08:00-09:00', '8:00 AM - 9:00 AM'),
    ('09:00-10:00', '9:00 AM - 10:00 AM'),
    ('10:00-11:00', '10:00 AM - 11:00 AM'),
    ('11:00-12:00', '11:00 AM - 12:00 PM'),
    ('12:00-13:00', '12:00 PM - 1:00 PM'),
    ('15:00-16:00', '3:00 PM - 4:00 PM'),
    ('16:00-17:00', '4:00 PM - 5:00 PM'),
    ('17:00-18:00', '5:00 PM - 6:00 PM'),
    ('18:00-19:00', '6:00 PM - 7:00 PM'),
]

TIME_SLOT_DISPLAY_MAP = dict(TIME_SLOT_CHOICES)
TIME_SLOT_VALUES = [slot for slot, _ in TIME_SLOT_CHOICES]

# ==================== COURSE DEFINITIONS ====================
COURSE_CHOICES = [
    ('MS-CIT', 'MS-CIT'),
    ('Tally', 'Tally'),
    ('Advance Excel', 'Advance Excel'),
    ('IOT', 'IOT'),
    ('Scratch', 'Scratch'),
    ('Other', 'Other'),
]

# ==================== GENDER DEFINITIONS ====================
GENDER_CHOICES = [
    ('Male', 'Male'),
    ('Female', 'Female'),
    ('Other', 'Other'),
]

# ==================== MARITAL STATUS DEFINITIONS ====================
MARITAL_STATUS_CHOICES = [
    ('Single', 'Single'),
    ('Married', 'Married'),
]

# ==================== PAYMENT MODE DEFINITIONS ====================
PAYMENT_MODE_CHOICES = [
    ('Cash', 'Cash'),
    ('UPI', 'UPI'),
    ('Card', 'Card'),
    ('Bank Transfer', 'Bank Transfer'),
]

# ==================== ATTENDANCE STATUS DEFINITIONS ====================
ATTENDANCE_STATUS_CHOICES = [
    ('P', 'Present'),
    ('A', 'Absent'),
    ('L', 'Leave'),
    ('H', 'Holiday'),
]

# ==================== BATCH TYPE DEFINITIONS ====================
BATCH_TYPE_CHOICES = [
    ('Theory', 'Theory'),
    ('Practical', 'Practical'),
]

# ==================== MONTH DEFINITIONS ====================
MONTH_CHOICES = [
    ('January', 'January'),
    ('February', 'February'),
    ('March', 'March'),
    ('April', 'April'),
    ('May', 'May'),
    ('June', 'June'),
    ('July', 'July'),
    ('August', 'August'),
    ('September', 'September'),
    ('October', 'October'),
    ('November', 'November'),
    ('December', 'December'),
]

# ==================== FORM CLASS MAPPING ====================
FORM_CONTROL_CLASS = 'form-control'
FORM_WIDGET_ATTRS = {
    'class': FORM_CONTROL_CLASS,
}

# ==================== PAGINATION ====================
DEFAULT_PAGE_SIZE = 10
STUDENTS_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100

# ==================== FILE UPLOAD SETTINGS ====================
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 MB
ALLOWED_DB_EXTENSIONS = ['db', 'sqlite', 'sqlite3']
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif']

# ==================== FINANCIAL SETTINGS ====================
MAX_PAYMENT_AMOUNT = 10000000  # 10 Million rupees
MIN_PAYMENT_AMOUNT = 0.01  # 1 paise
DEFAULT_TOTAL_FEES = 5000

# ==================== DUPLICATE CHECK WINDOW ====================
ENQUIRY_DUPLICATE_CHECK_MINUTES = 5  # Check for duplicates within 5 minutes

# ==================== DATE/TIME FORMATS ====================
DATE_FORMAT = '%d-%m-%Y'
DATE_ISO_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = '%d-%m-%Y %I:%M %p'
DATETIME_ISO_FORMAT = '%Y-%m-%d %H:%M:%S'

# ==================== MONTHS LIST (for reports) ====================
MONTHS_LIST = ['January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']

MONTHS_SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
