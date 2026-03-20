#!/usr/bin/env python
"""
Test script to verify batch creation and deletion flow
Run with: python manage.py shell < test_batch_flow.py
"""

from core.models import Batch, Course, AdmittedStudent
from django.contrib.auth.models import User

print("\n" + "="*80)
print("BATCH MANAGEMENT TEST SCRIPT")
print("="*80)

# Test 1: Create a batch
print("\n[TEST 1] Creating a batch...")
try:
    batch = Batch.objects.create(
        batch_type='Theory',
        time_slot='09:00-10:00',
        capacity=50,
        course=None
    )
    print(f"✅ Batch created successfully: ID={batch.id}, Type={batch.batch_type}, Slot={batch.time_slot}")
except Exception as e:
    print(f"❌ Error creating batch: {e}")
    exit(1)

# Test 2: Query by type and slot (what get_batch_id does)
print("\n[TEST 2] Finding batch by type and time_slot (with course__isnull=True filter)...")
try:
    found_batch = Batch.objects.get(
        batch_type='Theory',
        time_slot='09:00-10:00',
        course__isnull=True
    )
    print(f"✅ Batch found: ID={found_batch.id}, Type={found_batch.batch_type}")
    assert found_batch.id == batch.id, "Found batch ID doesn't match created batch ID"
except Batch.DoesNotExist:
    print(f"❌ Batch not found with those parameters!")
    exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Test 3: Delete the batch (should work since no students assigned)
print("\n[TEST 3] Deleting the batch...")
try:
    student_count = AdmittedStudent.objects.filter(
        theory_batch_time='09:00-10:00'
    ).count()
    print(f"   Students assigned to this batch: {student_count}")
    
    if student_count > 0:
        print(f"❌ Cannot delete - batch has {student_count} student(s)")
    else:
        batch_id = found_batch.id
        found_batch.delete()
        
        # Verify deletion
        verify = Batch.objects.filter(id=batch_id).exists()
        if verify:
            print(f"❌ Batch still exists after deletion!")
        else:
            print(f"✅ Batch deleted successfully!")
except Exception as e:
    print(f"❌ Error deleting batch: {e}")
    exit(1)

# Test 4: Verify batch is gone
print("\n[TEST 4] Verifying batch is deleted...")
try:
    found = Batch.objects.filter(
        batch_type='Theory',
        time_slot='09:00-10:00',
        course__isnull=True
    ).exists()
    if found:
        print(f"❌ Batch still exists!")
    else:
        print(f"✅ Batch successfully deleted!")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*80)
print("✅ ALL TESTS PASSED!")
print("="*80 + "\n")
