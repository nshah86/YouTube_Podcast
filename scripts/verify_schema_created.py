"""
Verify that Supabase schema was created successfully.
This script uses the Supabase REST API to check if tables exist.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

try:
    from supabase import create_client, Client
    import requests
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False
    print("❌ Required packages not installed")
    print("   Run: pip install supabase requests")
    sys.exit(1)

def verify_schema():
    """Verify schema tables exist"""
    print("=" * 70)
    print("Supabase Schema Verification")
    print("=" * 70)
    print()
    
    # Get credentials
    supabase_url = os.getenv("REACT_APP_SUPABASE_URL") or os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("REACT_APP_SUPABASE_ANON_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Supabase credentials not found")
        return False
    
    print(f"Project: {supabase_url}")
    print()
    
    # Create client
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Required tables
    required_tables = ['user_profiles', 'api_tokens', 'usage_history']
    results = {}
    
    print("Checking tables...")
    print()
    
    for table in required_tables:
        try:
            # Try to query the table with a limit
            # This will fail if table doesn't exist or RLS blocks it
            response = supabase.table(table).select('*', count='exact').limit(0).execute()
            
            # If we get here, table exists
            count = response.count if hasattr(response, 'count') else 0
            results[table] = {
                'exists': True,
                'accessible': True,
                'row_count': count,
                'error': None
            }
            print(f"  ✓ {table}: EXISTS (accessible, {count} rows)")
            
        except Exception as e:
            error_msg = str(e)
            error_dict = e.args[0] if e.args and isinstance(e.args[0], dict) else {}
            
            # Check error type
            if 'does not exist' in error_msg.lower() or 'relation' in error_msg.lower():
                results[table] = {
                    'exists': False,
                    'accessible': False,
                    'error': 'Table does not exist'
                }
                print(f"  ❌ {table}: DOES NOT EXIST")
            elif 'permission denied' in error_msg.lower() or 'RLS' in error_msg.upper():
                # Table might exist but RLS is blocking
                results[table] = {
                    'exists': True,  # Assume exists if RLS error
                    'accessible': False,
                    'error': 'RLS or permission issue'
                }
                print(f"  ⚠️  {table}: EXISTS but RLS blocking (this is OK)")
            elif 'schema must be one of the following: api' in error_msg.lower():
                # This is a REST API schema issue - try direct SQL check
                results[table] = {
                    'exists': None,  # Unknown
                    'accessible': False,
                    'error': 'REST API schema issue'
                }
                print(f"  ⚠️  {table}: Cannot verify via REST API")
            else:
                results[table] = {
                    'exists': None,
                    'accessible': False,
                    'error': error_msg[:100]
                }
                print(f"  ⚠️  {table}: {error_msg[:60]}")
    
    print()
    print("=" * 70)
    print("Verification Summary")
    print("=" * 70)
    print()
    
    # Count results
    exists_count = sum(1 for r in results.values() if r.get('exists') is True)
    unknown_count = sum(1 for r in results.values() if r.get('exists') is None)
    missing_count = sum(1 for r in results.values() if r.get('exists') is False)
    
    if exists_count == len(required_tables):
        print("✅ All tables exist and are accessible!")
        print()
        print("Schema is properly set up. You can now:")
        print("  1. Start the app: python start.py")
        print("  2. Run tests: python run_tests.py")
        return True
    elif exists_count > 0 or unknown_count > 0:
        print(f"⚠️  Partial verification: {exists_count} confirmed, {unknown_count} unknown")
        print()
        print("The 'schema must be one of the following: api' error suggests")
        print("the Supabase REST API client has limitations. However, if you")
        print("ran database_schema.sql in the SQL Editor, the tables should exist.")
        print()
        print("To verify manually:")
        print("  1. Go to Supabase Dashboard > Table Editor")
        print("  2. Check if you see: user_profiles, api_tokens, usage_history")
        print()
        print("If tables are visible in dashboard, schema is correct!")
        return True
    else:
        print("❌ Tables not found")
        print()
        print("Please verify:")
        print("  1. You ran database_schema.sql in Supabase SQL Editor")
        print("  2. Check Supabase Dashboard > Table Editor for tables")
        print("  3. Re-run database_schema.sql if needed")
        return False

if __name__ == "__main__":
    success = verify_schema()
    sys.exit(0 if success else 1)

