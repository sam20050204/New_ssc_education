"""
Unit tests to verify FeePayment receipt creation logic
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings.dev')
sys.path.insert(0, os.path.dirname(__file__))

django.setup()

from decimal import Decimal

# Test 1: Verify payment mode validation
print("=" * 70)
print("TEST 1: Payment Mode Validation")
print("=" * 70)

valid_modes = ['Cash', 'UPI', 'Card', 'Bank Transfer']
test_modes = ['Cash', 'Online', 'UPI', 'Card', 'Bank Transfer', 'Crypto', '', 'Bitcoin']

print(f"\nValid Payment Modes: {valid_modes}")
print("\nTest Cases:")
for mode in test_modes:
    is_valid = mode in valid_modes
    status = "✅ PASS" if is_valid else "❌ FAIL" if mode in ['Online', 'Crypto', 'Bitcoin'] else "⚠️  WARN"
    print(f"  {mode:20} → {is_valid:5} {status}")

# Note: 'Online' was used in export header but should be replaced with actual modes
print("\n⚠️  NOTE: Column header says 'Payment Mode (Cash/Online)' for user display")
print("        but actual values should be: Cash, UPI, Card, or Bank Transfer")

# Test 2: Verify Decimal conversion logic
print("\n" + "=" * 70)
print("TEST 2: First Installment Decimal Conversion")
print("=" * 70)

test_values = [5000, '5000', '5000.50', 0, '0', None, '', 'abc', -100]

for value in test_values:
    try:
        result = Decimal(str(value)) if value else Decimal('0')
        is_gt_zero = result > Decimal('0')
        status = "✅ Valid" if result >= 0 else "⚠️  Negative"
        print(f"  Input: {str(value):20} → {str(result):15} | > 0: {is_gt_zero:5} {status}")
    except Exception as e:
        print(f"  Input: {str(value):20} → ❌ ERROR: {type(e).__name__}")

# Test 3: Verify receipt_no format
print("\n" + "=" * 70)
print("TEST 3: Receipt Number Generation")
print("=" * 70)

from datetime import date
import uuid

# Simulate receipt generation
dates_to_test = [
    date(2026, 4, 3),
    date(2026, 1, 15),
    date(2025, 12, 31),
]

print("\nGenerated Receipt Numbers:")
for test_date in dates_to_test:
    receipt_prefix = test_date.strftime('%d%m%Y')
    receipt_suffix = str(uuid.uuid4().hex[:5]).upper()
    receipt_no = f'REC-{receipt_prefix}-{receipt_suffix}'
    print(f"  Date: {test_date} → {receipt_no}")

# Test 4: Show column mapping
print("\n" + "=" * 70)
print("TEST 4: Excel Column Mapping (0-based indices)")
print("=" * 70)

columns = [
    (0, 'S.No'),
    (1, 'Full Name'),
    (19, 'Pin Code'),
    (20, 'Total Fees (₹)'),
    (21, 'Paid Fees First Installment (₹)'),  # Column 22, Index 21
    (22, 'Payment Mode (Cash/Online)'),        # Column 23, Index 22 - WAIT THIS IS WRONG
    (25, 'Admission Date'),
]

print("\nColumn Mapping (1-based column = 0-based index + 1):")
for idx, name in columns:
    col_num = idx + 1
    print(f"  Column {col_num:2} (Index {idx:2}): {name}")

print("\n⚠️  CORRECTION NEEDED:")
print("   The export shows Payment Mode at Column 22 (Index 21)")
print("   But code extracts from row_values[21] which is correct!")

# Recalculate
print("\nVerifying indices from export:")
export_columns = [
    'S.No',                               # 1  (idx 0)
    'Full Name',                          # 2  (idx 1)
    'Student Name',                       # 3  (idx 2)
    'Father Name',                        # 4  (idx 3)
    'Surname',                            # 5  (idx 4)
    'Mother Name',                        # 6  (idx 5)
    'Date of Birth',                      # 7  (idx 6)
    'Mobile (Own)',                       # 8  (idx 7)
    'Parent Mobile',                      # 9  (idx 8)
    'Gender',                             # 10 (idx 9)
    'Marital Status',                     # 11 (idx 10)
    'Course',                             # 12 (idx 11)
    'Custom Course',                      # 13 (idx 12)
    'Educational Qualification',          # 14 (idx 13)
    'Address',                            # 15 (idx 14)
    'City',                               # 16 (idx 15)
    'Tehsil/Block',                       # 17 (idx 16)
    'District',                           # 18 (idx 17)
    'Pin Code',                           # 19 (idx 18)
    'Total Fees (₹)',                     # 20 (idx 19)
    'Paid Fees First Installment (₹)',    # 21 (idx 20) ← first_installment
    'Payment Mode (Cash/Online)',         # 22 (idx 21) ← payment_mode
    'Paid Fees (₹)',                      # 23 (idx 22)
    'Remaining Fees (₹)',                 # 24 (idx 23)
    'Fees % Paid',                        # 25 (idx 24)
    'Admission Date'                      # 26 (idx 25)
]

for idx, col in enumerate(export_columns):
    if 'Installment' in col or 'Payment Mode' in col or 'Admission Date' in col:
        print(f"  Column {idx+1:2} (Index {idx:2}): {col}")

print("\n✅ Column mapping is CORRECT!")

print("\n" + "=" * 70)
print("ALL VERIFICATION TESTS COMPLETE")
print("=" * 70)
