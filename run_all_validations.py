"""
Run all validation scripts in sequence.
This is the master validation script for production readiness.
"""

import subprocess
import sys


def run_script(script_name, description):
    """Run a Python script and return success status."""
    print(f"\n{'='*80}")
    print(f"Running: {description}")
    print(f"Script: {script_name}")
    print(f"{'='*80}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=False,
            text=True
        )
        
        success = result.returncode == 0
        
        if success:
            print(f"\n✅ {description} - PASSED")
        else:
            print(f"\n❌ {description} - FAILED")
        
        return success
    
    except Exception as e:
        print(f"\n❌ {description} - ERROR: {e}")
        return False


def main():
    """Run all validation scripts."""
    
    print("="*80)
    print("MASTER VALIDATION SUITE")
    print("="*80)
    print("\nThis will run all validation scripts to ensure production readiness.")
    print("Tests include:")
    print("  1. Price fix validation")
    print("  2. Unique items validation")
    print("  3. Comprehensive system test")
    print("\nStarting validation...\n")
    
    results = []
    
    # Test 1: Price Fix
    results.append({
        'name': 'Price Fix Validation',
        'passed': run_script('test_final_fix.py', 'Price Fix Validation')
    })
    
    # Test 2: Unique Items
    results.append({
        'name': 'Unique Items Validation',
        'passed': run_script('test_unique_items_fix.py', 'Unique Items Validation')
    })
    
    # Test 3: Comprehensive System Test
    results.append({
        'name': 'Comprehensive System Test',
        'passed': run_script('testing.py', 'Comprehensive System Test')
    })
    
    # Final Summary
    print(f"\n{'='*80}")
    print("VALIDATION SUMMARY")
    print(f"{'='*80}\n")
    
    all_passed = all(r['passed'] for r in results)
    
    for result in results:
        status = "✅ PASSED" if result['passed'] else "❌ FAILED"
        print(f"  {result['name']}: {status}")
    
    print(f"\n{'='*80}")
    
    if all_passed:
        print("✅✅✅ ALL VALIDATIONS PASSED ✅✅✅")
        print("\n🎉 System is PRODUCTION READY!")
        print("\nNext steps:")
        print("  1. Review debug_results.json for detailed metrics")
        print("  2. Generate reports: python test_reports_q2.py")
        print("  3. Deploy to production")
        print(f"{'='*80}\n")
        return 0
    else:
        print("❌ SOME VALIDATIONS FAILED")
        print("\n⚠️  System is NOT ready for production.")
        print("\nAction required:")
        print("  1. Review failed tests above")
        print("  2. Fix identified issues")
        print("  3. Re-run validation")
        print(f"{'='*80}\n")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
