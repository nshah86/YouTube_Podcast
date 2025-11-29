"""
Complete application validation including Supabase schema.
Runs all validation checks in sequence.
"""
import sys
import subprocess
from pathlib import Path

def run_validation(script_path, description):
    """Run a validation script and return result"""
    print("=" * 70)
    print(f"{description}")
    print("=" * 70)
    print()
    
    if not script_path.exists():
        print(f"WARNING: Script not found: {script_path.name}")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"⏱️  Validation timed out")
        return False
    except Exception as e:
        print(f"❌ Error running validation: {e}")
        return False

def main():
    """Run all validations"""
    print("=" * 70)
    print("VideoTranscript Pro - Complete Application Validation")
    print("=" * 70)
    print()
    
    # Use absolute paths
    project_root = Path(__file__).parent.parent
    validations = [
        (project_root / "validate_app.py", "1. Application Structure & Dependencies"),
        (project_root / "scripts" / "test_supabase_connection.py", "2. Supabase Connection Test"),
        (project_root / "scripts" / "verify_schema_created.py", "3. Database Schema Verification"),
    ]
    
    results = {}
    
    for script, description in validations:
        success = run_validation(script, description)
        results[description] = success
        print()
    
    # Summary
    print("=" * 70)
    print("Validation Summary")
    print("=" * 70)
    print()
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for desc, success in results.items():
        status = "PASS" if success else "FAIL"
        print(f"{status}: {desc}")
    
    print()
    print(f"Total: {passed}/{total} validations passed")
    print()
    
    if passed == total:
        print("SUCCESS: All validations passed! Application is ready.")
        print()
        print("Next steps:")
        print("  1. Start the app: python start.py")
        print("  2. Run automation tests: python run_tests.py")
        return 0
    else:
        print("WARNING: Some validations failed. Please review errors above.")
        print()
        print("Note: If you ran database_schema.sql in Supabase SQL Editor,")
        print("the schema should be created. The REST API verification may")
        print("have limitations, but tables should exist in Supabase Dashboard.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

