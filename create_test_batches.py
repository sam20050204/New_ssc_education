import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings')
django.setup()

from core.models import Batch

# Check if batches exist
existing = Batch.objects.filter(batch_type='Theory', course__isnull=True).count()
print(f"Existing Theory batches: {existing}")

if existing == 0:
    print("Creating test batches...")
    
    # Create Theory batches
    time_slots = [
        '08:00-09:00',
        '09:00-10:00',
        '10:00-11:00',
        '11:00-12:00',
    ]
    
    for slot in time_slots:
        batch, created = Batch.objects.get_or_create(
            batch_type='Theory',
            time_slot=slot,
            course=None,
            defaults={'capacity': 50}
        )
        if created:
            print(f"  Created Theory batch {batch.id}: {slot}, capacity={batch.capacity}")
        else:
            print(f"  Theory batch already exists: {slot}")
    
    # Create Practical batches
    for slot in time_slots:
        batch, created = Batch.objects.get_or_create(
            batch_type='Practical',
            time_slot=slot,
            course=None,
            defaults={'capacity': 40}
        )
        if created:
            print(f"  Created Practical batch {batch.id}: {slot}, capacity={batch.capacity}")
        else:
            print(f"  Practical batch already exists: {slot}")
    
    print("\nAll batches created!")
else:
    print("Batches already exist, no action needed")

# List all batches
print("\n=== Summary ===")
batches = Batch.objects.filter(course__isnull=True).order_by('batch_type', 'time_slot')
for batch in batches:
    print(f"ID: {batch.id} | Type: {batch.batch_type} | Slot: {batch.time_slot} | Capacity: {batch.capacity}")
