#!/usr/bin/env python
"""
Test script to verify finance details filters and sorting
Run with: python manage.py shell < test_finance_filters.py
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings')
django.setup()

from core.models import AdmittedStudent
from django.db.models import Q, F
from django.db.models.functions import ExtractYear

print("\n" + "="*80)
print("FINANCE DETAILS FILTERS TEST")
print("="*80)

# Test 1: Get all students
print("\n[TEST 1] All Students:")
all_students = AdmittedStudent.objects.all()
print(f"Total students: {all_students.count()}")
for student in all_students[:3]:
    print(f"  - {student.full_name} ({student.course}) | Mobile: {student.mobile_own} | Year: {student.admission_date.year if student.admission_date else 'N/A'}")

# Test 2: Get available years
print("\n[TEST 2] Available Years:")
available_years = (
    AdmittedStudent.objects
    .annotate(year=ExtractYear('admission_date'))
    .values_list('year', flat=True)
    .distinct()
    .order_by('-year')
)
print(f"Available years: {list(available_years)}")

# Test 3: Get available courses
print("\n[TEST 3] Available Courses:")
available_courses = (
    AdmittedStudent.objects
    .values_list('course', flat=True)
    .distinct()
    .order_by('course')
)
print(f"Available courses: {list(available_courses)}")

# Test 4: Filter by year
print("\n[TEST 4] Filter by Year:")
year = available_years[0] if available_years else None
if year:
    year_filtered = AdmittedStudent.objects.filter(admission_date__year=year)
    print(f"Students in year {year}: {year_filtered.count()}")
    for student in year_filtered[:2]:
        print(f"  - {student.full_name}")
else:
    print("No years available")

# Test 5: Filter by course
print("\n[TEST 5] Filter by Course:")
course = available_courses[0] if available_courses else None
if course:
    course_filtered = AdmittedStudent.objects.filter(course=course)
    print(f"Students in course '{course}': {course_filtered.count()}")
    for student in course_filtered[:2]:
        print(f"  - {student.full_name}")
else:
    print("No courses available")

# Test 6: Search filter by name
print("\n[TEST 6] Search Filter by Name:")
search_name = "a"  # Search for names containing 'a'
search_filtered = AdmittedStudent.objects.filter(
    Q(full_name__icontains=search_name) |
    Q(student_name__icontains=search_name) |
    Q(mobile_own__icontains=search_name)
)
print(f"Students matching '{search_name}': {search_filtered.count()}")
for student in search_filtered[:2]:
    print(f"  - {student.full_name}")

# Test 7: Combined filters (year + course + search)
print("\n[TEST 7] Combined Filters (Year + Course + Search):")
combined = AdmittedStudent.objects.all()
if year:
    combined = combined.filter(admission_date__year=year)
if course:
    combined = combined.filter(course=course)
if search_name:
    combined = combined.filter(
        Q(full_name__icontains=search_name) |
        Q(student_name__icontains=search_name) |
        Q(mobile_own__icontains=search_name)
    )
print(f"Combined filter results: {combined.count()}")
for student in combined[:2]:
    print(f"  - {student.full_name}")

# Test 8: Sorting by different fields
print("\n[TEST 8] Sorting Tests:")

# Sort by name
sorted_by_name = list(all_students)
sorted_by_name.sort(key=lambda x: x.full_name or '')
print(f"First 3 by name (A-Z): {[s.full_name for s in sorted_by_name[:3]]}")

# Sort by course
sorted_by_course = list(all_students)
sorted_by_course.sort(key=lambda x: x.course)
print(f"First 3 by course: {[(s.full_name, s.course) for s in sorted_by_course[:3]]}")

# Sort by mobile
sorted_by_mobile = list(all_students)
sorted_by_mobile.sort(key=lambda x: x.mobile_own or '')
print(f"First 3 by mobile: {[(s.full_name, s.mobile_own) for s in sorted_by_mobile[:3]]}")

print("\n" + "="*80)
print("✅ ALL FILTER TESTS COMPLETED SUCCESSFULLY")
print("="*80 + "\n")
