#!/usr/bin/env python
"""
Batch Deletion Feature - Verification Script
Run this to verify all components are in place and working
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def verify_imports():
    """Verify all required imports work"""
    print("\n" + "="*80)
    print("STEP 1: Verifying Imports")
    print("="*80)
    
    try:
        from core.models import Batch, AdmittedStudent
        print("✅ Batch and AdmittedStudent models imported successfully")
    except ImportError as e:
        print(f"❌ Error importing models: {e}")
        return False
    
    try:
        from django.http import JsonResponse
        print("✅ JsonResponse imported successfully")
    except ImportError as e:
        print(f"❌ Error importing JsonResponse: {e}")
        return False
    
    try:
        from django.contrib.auth.decorators import login_required
        print("✅ Decorators imported successfully")
    except ImportError as e:
        print(f"❌ Error importing decorators: {e}")
        return False
    
    return True


def verify_views():
    """Verify view functions exist and are callable"""
    print("\n" + "="*80)
    print("STEP 2: Verifying Views")
    print("="*80)
    
    try:
        from core import views
        
        # Check get_batch_id exists
        if hasattr(views, 'get_batch_id'):
            print("✅ get_batch_id view found")
        else:
            print("❌ get_batch_id view NOT found")
            return False
        
        # Check delete_batch exists
        if hasattr(views, 'delete_batch'):
            print("✅ delete_batch view found")
        else:
            print("❌ delete_batch view NOT found")
            return False
        
        # Check create_batch exists
        if hasattr(views, 'create_batch'):
            print("✅ create_batch view found")
        else:
            print("❌ create_batch view NOT found")
            return False
        
        # Check get_batch_list exists
        if hasattr(views, 'get_batch_list'):
            print("✅ get_batch_list view found")
        else:
            print("❌ get_batch_list view NOT found")
            return False
        
        return True
    
    except Exception as e:
        print(f"❌ Error verifying views: {e}")
        return False


def verify_urls():
    """Verify URL patterns are registered"""
    print("\n" + "="*80)
    print("STEP 3: Verifying URL Routes")
    print("="*80)
    
    try:
        from core.urls import urlpatterns
        
        # Extract URL patterns
        url_list = []
        for pattern in urlpatterns:
            try:
                url_list.append(str(pattern.pattern))
            except:
                pass
        
        urls_to_check = [
            'batch/create/',
            'batch/<int:batch_id>/delete/',
            'batch/list/',
            'batch/get-id/'
        ]
        
        for url in urls_to_check:
            if any(url in str(u) for u in urlpatterns):
                print(f"✅ Route '{url}' found")
            else:
                # Try pattern matching
                found = False
                for pattern in urlpatterns:
                    if url.replace('<int:batch_id>', '') in str(pattern.pattern):
                        found = True
                        break
                if found:
                    print(f"✅ Route '{url}' found")
                else:
                    print(f"❌ Route '{url}' NOT found")
                    return False
        
        return True
    
    except Exception as e:
        print(f"❌ Error verifying URLs: {e}")
        return False


def verify_models():
    """Verify Batch model has required fields"""
    print("\n" + "="*80)
    print("STEP 4: Verifying Batch Model")
    print("="*80)
    
    try:
        from core.models import Batch
        
        required_fields = ['batch_type', 'time_slot', 'course', 'capacity', 'id']
        
        batch_fields = [f.name for f in Batch._meta.get_fields()]
        
        for field in required_fields:
            if field in batch_fields:
                print(f"✅ Field '{field}' exists in Batch model")
            else:
                print(f"❌ Field '{field}' NOT found in Batch model")
                return False
        
        return True
    
    except Exception as e:
        print(f"❌ Error verifying model: {e}")
        return False


def verify_database():
    """Verify database connection works"""
    print("\n" + "="*80)
    print("STEP 5: Verifying Database Connection")
    print("="*80)
    
    try:
        from core.models import Batch
        
        # Try to count batches
        count = Batch.objects.count()
        print(f"✅ Database connection works (Found {count} batches)")
        
        return True
    
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return False


def verify_crud_flow():
    """Verify full CRUD flow works"""
    print("\n" + "="*80)
    print("STEP 6: Verifying CRUD Flow")
    print("="*80)
    
    try:
        from core.models import Batch, AdmittedStudent
        
        # Create
        print("  Testing CREATE...")
        batch = Batch.objects.create(
            batch_type='Theory',
            time_slot='09:00-10:00',
            capacity=50,
            course=None
        )
        print(f"  ✅ Batch created: ID={batch.id}")
        
        # Read
        print("  Testing READ...")
        found = Batch.objects.get(
            batch_type='Theory',
            time_slot='09:00-10:00',
            course__isnull=True
        )
        assert found.id == batch.id
        print(f"  ✅ Batch found: ID={found.id}")
        
        # Check student count
        print("  Testing VALIDATION...")
        student_count = AdmittedStudent.objects.filter(
            theory_batch_time='09:00-10:00'
        ).count()
        print(f"  ✅ Student count check: {student_count} students")
        
        # Delete
        print("  Testing DELETE...")
        batch.delete()
        exists = Batch.objects.filter(id=batch.id).exists()
        assert not exists
        print(f"  ✅ Batch deleted successfully")
        
        return True
    
    except Exception as e:
        print(f"❌ Error in CRUD flow: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_verification():
    """Run all verifications"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "BATCH DELETION FEATURE VERIFICATION" + " "*24 + "║")
    print("╚" + "="*78 + "╝")
    
    checks = [
        ("Imports", verify_imports),
        ("Views", verify_views),
        ("URLs", verify_urls),
        ("Models", verify_models),
        ("Database", verify_database),
        ("CRUD Flow", verify_crud_flow),
    ]
    
    results = []
    
    for name, check in checks:
        try:
            result = check()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Unexpected error in {name}: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print("\n" + "="*80)
    print(f"Result: {passed}/{total} checks passed")
    print("="*80)
    
    if passed == total:
        print("\n✅✅✅ ALL VERIFICATION CHECKS PASSED! ✅✅✅")
        print("\nBatch deletion feature is ready to use!")
        print("Go to: http://127.0.0.1:8000/batch/overview/")
        return 0
    else:
        print(f"\n❌ {total - passed} check(s) failed")
        print("Please review the errors above")
        return 1


if __name__ == '__main__':
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings')
    django.setup()
    
    exit_code = run_verification()
    sys.exit(exit_code)
