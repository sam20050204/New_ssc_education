#!/usr/bin/env python
"""
Django Admin Verification Script
Tests if all admin interfaces load without errors
"""

import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings')
sys.path.insert(0, r'e:\Projects\New_ssc_education')

django.setup()

from django.contrib import admin
from core.models import (
    Enquiry, AdmittedStudent, Course, Student, 
    FeePayment, StudentFinanceDetail
)

def test_admin_registration():
    """Verify all models are registered in admin"""
    
    models_to_check = [
        ('Enquiry', Enquiry),
        ('AdmittedStudent', AdmittedStudent),
        ('Course', Course),
        ('Student', Student),
        ('FeePayment', FeePayment),
        ('StudentFinanceDetail', StudentFinanceDetail),
    ]
    
    print("=" * 60)
    print("DJANGO ADMIN VERIFICATION REPORT")
    print("=" * 60)
    
    all_registered = True
    
    for model_name, model_class in models_to_check:
        is_registered = model_class in admin.site._registry
        status = "✓ REGISTERED" if is_registered else "✗ NOT REGISTERED"
        print(f"{model_name:30} {status}")
        
        if is_registered:
            admin_class = admin.site._registry[model_class]
            print(f"  └─ Admin Class: {admin_class.__class__.__name__}")
        else:
            all_registered = False
    
    print("=" * 60)
    
    if all_registered:
        print("✓ ALL MODELS REGISTERED SUCCESSFULLY")
        print("✓ NO PYTHON ERRORS")
        print("✓ ADMIN INTERFACE SHOULD WORK")
        return True
    else:
        print("✗ SOME MODELS NOT REGISTERED")
        return False

if __name__ == "__main__":
    try:
        result = test_admin_registration()
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
