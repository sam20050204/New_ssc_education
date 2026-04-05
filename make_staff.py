#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings.dev')
django.setup()

from django.contrib.auth.models import User

# Get all users and make them staff if needed
users = User.objects.all()
print(f"Total users: {users.count()}\n")

for user in users:
    status = "✅ Already staff" if user.is_staff else "🔄 Making staff"
    print(f"{status}: {user.username} (is_staff={user.is_staff})")
    if not user.is_staff:
        user.is_staff = True
        user.save()

# Get updated users
users = User.objects.all()
print(f"\nAfter update:")
for user in users:
    print(f"✅ {user.username}: is_staff={user.is_staff}")
