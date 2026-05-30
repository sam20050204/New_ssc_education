"""
Utility Functions for Core Application
Centralized helper functions used across views, forms, and templates
"""

from datetime import date, datetime, timedelta
from decimal import Decimal

from django.core.cache import cache
from django.db.models import Q

from .constants import TIME_SLOT_DISPLAY_MAP

# ==================== TIME SLOT UTILITIES ====================


def get_time_slot_display(time_slot):
    """Get display name for a time slot"""
    return TIME_SLOT_DISPLAY_MAP.get(time_slot, time_slot or "Not Assigned")


def format_all_time_slots(time_slots):
    """Convert raw time slots to display format"""
    return [(slot, get_time_slot_display(slot)) for slot in time_slots]


# ==================== COURSE UTILITIES ====================


def get_course_display(course, custom_course=""):
    """Get display name for course, handling 'Other' type"""
    if course == "Other" and custom_course:
        return custom_course
    return course or "N/A"


# ==================== SEARCH AND FILTER UTILITIES ====================


def apply_search_filter(queryset, search_query, search_fields):
    """
    Apply search filter to queryset

    Args:
        queryset: Django queryset to filter
        search_query: Search string
        search_fields: List of field names to search in (e.g., ['name', 'mobile'])

    Returns:
        Filtered queryset

    Example:
        queryset = apply_search_filter(
            AdmittedStudent.objects.all(),
            search_query,
            ['full_name', 'mobile_own']
        )
    """
    if not search_query:
        return queryset

    q_objects = Q()
    for field in search_fields:
        q_objects |= Q(**{f"{field}__icontains": search_query})

    return queryset.filter(q_objects)


def apply_date_filters(queryset, date_field, month=None, year=None):
    """
    Apply month and year filters to queryset

    Args:
        queryset: Django queryset
        date_field: Name of date field to filter on
        month: Month number (1-12) or None
        year: Year or None

    Returns:
        Filtered queryset
    """
    if month:
        queryset = queryset.filter(**{f"{date_field}__month": month})
    if year:
        queryset = queryset.filter(**{f"{date_field}__year": year})

    return queryset


# ==================== FINANCIAL UTILITIES ====================


def calculate_remaining_fees(total_fees, paid_fees):
    """Calculate remaining fees"""
    total = Decimal(str(total_fees or 0))
    paid = Decimal(str(paid_fees or 0))
    return total - paid


def calculate_fees_percentage(paid_fees, total_fees):
    """Calculate fees percentage paid"""
    total = Decimal(str(total_fees or 0))
    paid = Decimal(str(paid_fees or 0))

    if total > 0:
        return (paid / total) * Decimal("100")
    return Decimal("0")


def calculate_student_profit(student):
    """
    Calculate profit for a single student.
    Profit = (Total Fees Paid By Learner) - (Total Fees Paid to MKCL)

    Args:
        student: AdmittedStudent instance

    Returns:
        Decimal profit amount
    """
    from .models import StudentFinanceDetail

    finance_detail = getattr(student, "finance_detail", None)
    if finance_detail is None:
        finance_detail, _ = StudentFinanceDetail.objects.get_or_create(student=student)

    return Decimal(finance_detail.profit or 0)


def calculate_total_profit(student_queryset):
    """
    Calculate total profit for a queryset of students.

    Args:
        student_queryset: QuerySet of AdmittedStudent instances

    Returns:
        Decimal total profit
    """
    total = Decimal("0.00")
    for student in student_queryset:
        total += calculate_student_profit(student)
    return total


def number_to_words(num):
    """
    Convert number to words for Indian currency

    Args:
        num: Numeric value (int or float)

    Returns:
        String representation in words (e.g., "Five Thousand Two Hundred Rupees Only")
    """
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    teens = [
        "Ten",
        "Eleven",
        "Twelve",
        "Thirteen",
        "Fourteen",
        "Fifteen",
        "Sixteen",
        "Seventeen",
        "Eighteen",
        "Nineteen",
    ]

    if num == 0:
        return "Zero Rupees Only"

    def convert_less_than_thousand(n):
        if n == 0:
            return ""

        result = ""

        if n >= 100:
            result += ones[n // 100] + " Hundred "
            n %= 100

        if n >= 20:
            result += tens[n // 10] + " "
            n %= 10
        elif n >= 10:
            result += teens[n - 10] + " "
            return result

        if n > 0:
            result += ones[n] + " "

        return result

    rupees = int(num)
    paise = int(round((num - rupees) * 100))

    result = ""

    if rupees >= 10000000:
        result += convert_less_than_thousand(rupees // 10000000) + "Crore "
        rupees %= 10000000

    if rupees >= 100000:
        result += convert_less_than_thousand(rupees // 100000) + "Lakh "
        rupees %= 100000

    if rupees >= 1000:
        result += convert_less_than_thousand(rupees // 1000) + "Thousand "
        rupees %= 1000

    if rupees > 0:
        result += convert_less_than_thousand(rupees)

    result += "Rupees"

    if paise > 0:
        result += " and " + convert_less_than_thousand(paise) + "Paise"

    result += " Only"

    return result.strip()


# ==================== BATCH UTILITIES ====================


def get_batch_students_queryset(batch_type, time_slot):
    """
    Get students for a specific batch

    Args:
        batch_type: 'Theory' or 'Practical'
        time_slot: Time slot value

    Returns:
        Queryset of AdmittedStudent
    """
    from .models import AdmittedStudent

    if batch_type == "Theory":
        return AdmittedStudent.objects.filter(theory_batch_time=time_slot).order_by("full_name")
    else:  # Practical
        return AdmittedStudent.objects.filter(practical_batch_time=time_slot).order_by("full_name")


def get_batch_strength(batch_type, time_slot):
    """Get number of students in a batch"""
    return get_batch_students_queryset(batch_type, time_slot).count()


# ==================== ATTENDANCE UTILITIES ====================


def get_attendance_stats(student):
    """
    Get attendance statistics for a student

    Args:
        student: AdmittedStudent instance

    Returns:
        Dict with attendance stats
    """
    from django.db.models import Q

    attendance_records = student.attendance_records.all()
    total_records = attendance_records.count()

    present_count = attendance_records.filter(Q(theory_attendance="P") | Q(practical_attendance="P")).count()

    absent_count = total_records - present_count

    if total_records > 0:
        percentage = round((present_count / total_records) * 100, 2)
    else:
        percentage = 0

    return {"total": total_records, "present": present_count, "absent": absent_count, "percentage": percentage}


# ==================== DATE UTILITIES ====================


def get_available_years_from_field(model, date_field):
    """
    Get all unique years from a date field

    Args:
        model: Django model class
        date_field: Name of date field

    Returns:
        QuerySet of years in descending order
    """
    from django.db.models.functions import ExtractYear

    return (
        model.objects.annotate(year=ExtractYear(date_field)).values_list("year", flat=True).distinct().order_by("-year")
    )


def format_date(date_obj, format_str="%d-%m-%Y"):
    """Format date object to string"""
    if not date_obj:
        return ""
    return date_obj.strftime(format_str)


def days_ago(num_days):
    """Get date from N days ago"""
    return date.today() - timedelta(days=num_days)


# ==================== MODEL UTILITIES ====================


def get_or_create_finance_detail(student):
    """
    Get or create StudentFinanceDetail for student with defaults

    Args:
        student: AdmittedStudent instance

    Returns:
        StudentFinanceDetail instance
    """
    from .models import StudentFinanceDetail

    finance_detail, created = StudentFinanceDetail.objects.get_or_create(
        student=student,
        defaults={
            "first_installment": Decimal("0.00"),
            "second_installment": Decimal("0.00"),
            "third_installment": Decimal("0.00"),
            "fourth_installment": Decimal("0.00"),
            "fifth_installment": Decimal("0.00"),
            "fees_paid_to_mkcl_1": Decimal("0.00"),
            "fees_paid_to_mkcl_2": Decimal("0.00"),
        },
    )
    return finance_detail


# ==================== EXPORT UTILITIES ====================


def generate_timestamp_filename(prefix="export"):
    """Generate filename with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}"


# ==================== VALIDATION UTILITIES ====================


def is_valid_mobile(mobile):
    """Validate Indian mobile number"""
    if not mobile:
        return False

    mobile = str(mobile).strip()

    # Must be 10 digits
    if not mobile.isdigit() or len(mobile) != 10:
        return False

    # Must start with 6-9 (Indian mobile numbers)
    if mobile[0] not in "6789":
        return False

    return True


def is_valid_pincode(pincode):
    """Validate Indian pin code"""
    if not pincode:
        return False

    pincode = str(pincode).strip()

    # Must be 6 digits
    if not pincode.isdigit() or len(pincode) != 6:
        return False

    return True


# ==================== CACHING UTILITIES ====================


def get_cached_courses(cache_timeout=300):
    """
    Get cached list of all courses

    Args:
        cache_timeout: Cache duration in seconds (default: 5 minutes)

    Returns:
        QuerySet of Course objects ordered by name
    """
    cache_key = "courses_list"
    courses = cache.get(cache_key)

    if courses is None:
        from .models import Course

        courses = list(Course.objects.all().order_by("name"))
        cache.set(cache_key, courses, cache_timeout)

    return courses


def get_cached_time_slots(cache_timeout=300):
    """
    Get cached list of configured time slots.

    Args:
        cache_timeout: Cache duration in seconds (default: 5 minutes)

    Returns:
        List of tuple pairs used by form and filter dropdowns.
    """
    cache_key = "time_slots_list"
    time_slots = cache.get(cache_key)

    if time_slots is None:
        time_slots = list(TIME_SLOT_DISPLAY_MAP.items())
        cache.set(cache_key, time_slots, cache_timeout)

    return time_slots


def get_cached_available_years(cache_timeout=3600):
    """
    Get cached list of available admission years

    Args:
        cache_timeout: Cache duration in seconds (default: 1 hour)

    Returns:
        List of years
    """
    cache_key = "available_years"
    years = cache.get(cache_key)

    if years is None:
        from django.db.models.functions import ExtractYear

        from .models import AdmittedStudent

        years = list(
            AdmittedStudent.objects.annotate(year=ExtractYear("admission_date"))
            .values_list("year", flat=True)
            .distinct()
            .order_by("-year")
        )
        cache.set(cache_key, years, cache_timeout)

    return years


def invalidate_course_cache():
    """Invalidate course cache when courses are added/updated"""
    cache.delete("courses_list")


def invalidate_admission_cache():
    """Invalidate admission-related caches when admissions are added/updated"""
    cache.delete("available_years")
