import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings.dev')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

# Create a test client
client = Client()

# Create a test user if needed
try:
    user = User.objects.get(username='admin')
except User.DoesNotExist:
    user = User.objects.create_superuser('admin', 'admin@test.com', 'admin123')

# Login
client.login(username='admin', password='admin123')

# Try to access dashboard
response = client.get('/dashboard/')

print(f"Dashboard Status Code: {response.status_code}")
if response.status_code == 200:
    print("✅ Dashboard page is working!")
else:
    print(f"❌ Dashboard error: {response.status_code}")
    print(response.content[:500])
