#!/usr/bin/env python
import os
import sys
import django
from django.test import Client
from django.contrib.auth.models import User

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings.dev')
sys.path.insert(0, 'e:\\Projects\\New_ssc_education')
django.setup()

# Create a test client
client = Client()

# Try to access the endpoint
print("Testing /admission/import-photos/ endpoint...")
response = client.get('/admission/import-photos/')
print(f"GET Response Status: {response.status_code}")

# Try POST without login
print("\nTesting POST without login...")
response = client.post('/admission/import-photos/')
print(f"POST Response Status: {response.status_code}")
print(f"Response: {response.content[:200]}")

# Create or get admin user
user, created = User.objects.get_or_create(username='admin')
if created:
    user.set_password('admin')
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print("\nCreated admin user")
else:
    print("\nAdmin user exists")

# Login and try
client.login(username='admin', password='admin')
print("\nLoggedIn as admin")

# Try POST with login but no file
print("\nTesting POST with login but no file...")
response = client.post('/admission/import-photos/')
print(f"POST Response Status: {response.status_code}")
print(f"Response: {response.content[:500]}")
