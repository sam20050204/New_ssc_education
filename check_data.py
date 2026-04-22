import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings.dev')
django.setup()

from core.models import AdmittedStudent

total_students = AdmittedStudent.objects.count()
print(f"Total Admitted Students: {total_students}")

# Show first few students
students = AdmittedStudent.objects.all()[:5]
for student in students:
    print(f"  - {student.full_name} | Admission Date: {student.admission_date}")
