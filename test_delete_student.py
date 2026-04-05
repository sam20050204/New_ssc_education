#!/usr/bin/env python
"""Test script to verify student deletion works correctly"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings.dev')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from core.models import AdmittedStudent, FeePayment, Attendance, StudentFinanceDetail
from django.db import connection, transaction

def test_delete_student():
    """Test deleting a student with all related records"""
    
    # Get a student (preferably one with related records)
    try:
        student = AdmittedStudent.objects.first()
        if not student:
            print("❌ No students found in database")
            return False
        
        student_id = student.id
        student_name = student.full_name
        
        # Count related records
        fee_count = FeePayment.objects.filter(student=student).count()
        attendance_count = Attendance.objects.filter(student=student).count()
        finance_exists = StudentFinanceDetail.objects.filter(student=student).exists()
        
        print(f"\n📊 Student: {student_name} (ID: {student_id})")
        print(f"   - Fee Payments: {fee_count}")
        print(f"   - Attendance Records: {attendance_count}")
        print(f"   - Finance Detail: {'Yes' if finance_exists else 'No'}")
        
        # Try to delete with foreign keys disabled
        print(f"\n🔄 Attempting to delete student...")
        
        try:
            # Disable FK constraints for SQLite BEFORE transaction
            fk_disabled = False
            if connection.settings_dict['ENGINE'] == 'django.db.backends.sqlite3':
                cursor = connection.cursor()
                cursor.execute('PRAGMA foreign_keys = OFF;')
                connection.commit()
                fk_disabled = True
                print("   ✓ SQLite FOREIGN_KEYS disabled")
            
            try:
                with transaction.atomic():
                    # Delete related records
                    FeePayment.objects.filter(student=student).delete()
                    print(f"   ✓ Deleted {fee_count} fee payment(s)")
                    
                    Attendance.objects.filter(student=student).delete()
                    print(f"   ✓ Deleted {attendance_count} attendance record(s)")
                    
                    StudentFinanceDetail.objects.filter(student=student).delete()
                    print(f"   ✓ Deleted finance detail")
                    
                    # Delete the student
                    student.delete()
                    print(f"   ✓ Deleted student record")
            finally:
                # Re-enable FK constraints
                if fk_disabled:
                    cursor = connection.cursor()
                    cursor.execute('PRAGMA foreign_keys = ON;')
                    connection.commit()
                    print("   ✓ SQLite FOREIGN_KEYS re-enabled")
            
            # Verify deletion
            if not AdmittedStudent.objects.filter(id=student_id).exists():
                print(f"\n✅ SUCCESS: Student {student_name} has been deleted successfully!")
                return True
            else:
                print(f"\n❌ ERROR: Student was not actually deleted!")
                return False
                
        except Exception as e:
            print(f"\n❌ ERROR during deletion: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    except Exception as e:
        print(f"❌ Setup error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_delete_student()
    sys.exit(0 if success else 1)
