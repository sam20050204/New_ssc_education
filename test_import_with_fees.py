"""
Test script to verify FeePayment receipt creation during import
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings.dev')
sys.path.insert(0, os.path.dirname(__file__))

django.setup()

from core.models import AdmittedStudent, FeePayment
from decimal import Decimal
from datetime import date

# Test 1: Check if recent admissions have fee payment records
print("=" * 60)
print("TEST 1: Checking for FeePayment records")
print("=" * 60)

recent_admissions = AdmittedStudent.objects.order_by('-admission_date')[:5]
print(f"\nRecent {len(recent_admissions)} admissions:")

for admission in recent_admissions:
    print(f"\n  Student: {admission.full_name}")
    print(f"  Total Fees: ₹{admission.total_fees}")
    print(f"  First Installment: ₹{admission.first_installment}")
    print(f"  Paid Fees: ₹{admission.paid_fees}")
    print(f"  Admission Date: {admission.admission_date}")
    
    # Check for fee payments
    fee_payments = FeePayment.objects.filter(student=admission)
    if fee_payments.exists():
        print(f"  ✅ Fee Payments ({fee_payments.count()}):")
        for payment in fee_payments:
            print(f"     - Receipt: {payment.receipt_no}")
            print(f"     - Amount: ₹{payment.amount}")
            print(f"     - Mode: {payment.payment_mode}")
            print(f"     - Date: {payment.payment_date}")
    else:
        print(f"  ⚠️  No fee payments found")

# Test 2: Verify payment mode is being saved correctly
print("\n" + "=" * 60)
print("TEST 2: Checking payment modes")
print("=" * 60)

all_fee_payments = FeePayment.objects.all().order_by('-created_at')[:10]
print(f"\nLast {len(all_fee_payments)} fee payments:")

payment_modes = {}
for payment in all_fee_payments:
    mode = payment.payment_mode
    payment_modes[mode] = payment_modes.get(mode, 0) + 1
    print(f"  {payment.receipt_no}: {payment.payment_mode} - ₹{payment.amount}")

print(f"\nPayment Mode Summary:")
for mode, count in payment_modes.items():
    print(f"  {mode}: {count}")

# Test 3: Verify receipt_no is unique
print("\n" + "=" * 60)
print("TEST 3: Checking receipt_no uniqueness")
print("=" * 60)

all_receipts = FeePayment.objects.values_list('receipt_no', flat=True)
unique_receipts = len(set(all_receipts))
total_receipts = len(all_receipts)

print(f"\nTotal receipts: {total_receipts}")
print(f"Unique receipts: {unique_receipts}")

if unique_receipts == total_receipts:
    print("✅ All receipt numbers are unique")
else:
    print("⚠️ Duplicate receipt numbers found!")
    duplicates = [r for r in all_receipts if list(all_receipts).count(r) > 1]
    print(f"   Duplicates: {set(duplicates)}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
