#!/usr/bin/env python
from PIL import Image
import os
import zipfile
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings.dev')
django.setup()

from core.models import AdmittedStudent

# Create test images directory
test_dir = 'test_photos'
if os.path.exists(test_dir):
    import shutil
    shutil.rmtree(test_dir)
os.makedirs(test_dir)

# Get first 3 students
students = list(AdmittedStudent.objects.all()[:3])

if not students:
    print("No students found in database!")
else:
    for student in students:
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='blue')
        filename = os.path.join(test_dir, f'{student.surname} {student.student_name}.jpg')
        img.save(filename)
        print(f'Created: {filename}')

    # Create ZIP file
    with zipfile.ZipFile('test_photos.zip', 'w') as zipf:
        for file in os.listdir(test_dir):
            file_path = os.path.join(test_dir, file)
            zipf.write(file_path, arcname=file)

    print(f'Created ZIP: test_photos.zip')

    # Show the files in the ZIP
    with zipfile.ZipFile('test_photos.zip', 'r') as zipf:
        print(f'ZIP contents:')
        for name in zipf.namelist():
            print(f'  - {name}')
