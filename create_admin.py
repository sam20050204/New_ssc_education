#!/usr/bin/env python
"""
Script to create admin superuser
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings')
django.setup()

from django.contrib.auth.models import User

# Delete existing admin if exists
User.objects.filter(username='admin').delete()

# Create new superuser with password
user = User.objects.create_superuser(username='admin', email='admin@ssc.com', password='admin123')
print(f"[OK] Superuser created: {user.username}")
print(f"[OK] Email: {user.email}")
print(f"[OK] Is staff: {user.is_staff}")
print(f"[OK] Is superuser: {user.is_superuser}")
print(f"\n[INFO] Use these credentials to login:")
print(f"  Username: admin")
print(f"  Password: admin123")
