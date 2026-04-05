#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings.dev')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
import zipfile
import io
from PIL import Image

# Create or get a staff user
user, created = User.objects.get_or_create(
    username='teststaff',
    defaults={
        'email': 'teststaff@example.com',
        'is_staff': True,
        'is_superuser': False
    }
)
if created:
    user.set_password('testpass123')
    user.save()
    print(f"✅ Created staff user: {user.username}")
else:
    print(f"✅ Using existing staff user: {user.username}")

# Create a client and login
client = Client()
login_success = client.login(username='teststaff', password='testpass123')
print(f"✅ Login successful: {login_success}")

# Create a test ZIP file in memory
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
    # Get a student
    from core.models import AdmittedStudent
    students = list(AdmittedStudent.objects.all()[:1])
    
    if students:
        student = students[0]
        # Create test image
        img = Image.new('RGB', (100, 100), color='red')
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='JPEG')
        img_buffer.seek(0)
        
        # Add to ZIP
        photo_name = f'{student.surname} {student.student_name}.jpg'
        zip_file.writestr(photo_name, img_buffer.getvalue())
        print(f"✅ Created test image in ZIP: {photo_name}")
    else:
        print("❌ No students found in database!")
        exit(1)

zip_buffer.seek(0)

# Test the endpoint
from django.test import TestCase
response = client.post(
    '/admission/import-photos/',
    {'zip_file': zip_buffer},
    format='multipart'
)

print(f"\n📡 Response Status: {response.status_code}")
print(f"📡 Response Type: {response.get('Content-Type')}")
print(f"📡 Response Content: {response.content[:500]}")

if response.status_code == 200:
    import json
    data = json.loads(response.content)
    print(f"\n✅ Success: {data}")
else:
    print(f"\n❌ Error: {response.content}")
