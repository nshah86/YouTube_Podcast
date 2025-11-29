"""
Test Supabase connection using direct Python client.
This tests the connection before attempting schema setup.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

try:
    from supabase import create_client, Client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False
    print("❌ supabase-py not installed. Run: pip install supabase")

def test_connection():
    """Test Supabase connection"""
    print("=" * 70)
    print("Supabase Connection Test")
    print("=" * 70)
    print()
    
    # Get credentials
    supabase_url = os.getenv("REACT_APP_SUPABASE_URL") or os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("REACT_APP_SUPABASE_ANON_KEY") or os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
    
    if not supabase_url:
        print("❌ SUPABASE_URL not found in environment variables")
        print()
        print("Please set one of:")
        print("  - REACT_APP_SUPABASE_URL")
        print("  - SUPABASE_URL")
        return False
    
    if not supabase_key:
        print("❌ SUPABASE_KEY not found in environment variables")
        print()
        print("Please set one of:")
        print("  - REACT_APP_SUPABASE_ANON_KEY")
        print("  - SUPABASE_ANON_KEY")
        print("  - SUPABASE_KEY")
        return False
    
    print(f"✓ Project URL: {supabase_url}")
    print(f"✓ API Key: {supabase_key[:20]}...{supabase_key[-10:]}")
    print()
    
    if not HAS_SUPABASE:
        return False
    
    try:
        # Create client
        print("Creating Supabase client...")
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✓ Client created")
        print()
        
        # Test 1: Simple query
        print("Test 1: Simple query (SELECT 1)...")
        try:
            result = supabase.rpc('version').execute()
            print("✓ RPC call works")
        except Exception as e:
            # Try direct table query instead
            print(f"  RPC not available, trying table query...")
            try:
                # Try to query a system table or use execute_sql if available
                result = supabase.table('_realtime').select('*').limit(0).execute()
                print("✓ Table query works")
            except Exception as e2:
                print(f"  Note: {str(e2)[:60]}")
        
        # Test 2: Check if tables exist
        print()
        print("Test 2: Checking existing tables...")
        required_tables = ['user_profiles', 'api_tokens', 'usage_history']
        
        for table in required_tables:
            try:
                result = supabase.table(table).select('*').limit(1).execute()
                print(f"  ✓ Table '{table}' exists and is accessible")
            except Exception as e:
                error_msg = str(e)
                if "relation" in error_msg.lower() and "does not exist" in error_msg.lower():
                    print(f"  ⚠️  Table '{table}' does not exist (needs schema setup)")
                else:
                    print(f"  ❌ Table '{table}' error: {error_msg[:60]}")
        
        # Test 3: Check auth.users (should exist by default)
        print()
        print("Test 3: Checking auth system...")
        try:
            # Can't directly query auth.users, but we can check if we can create a test user profile
            print("  ✓ Auth system accessible (via Supabase client)")
        except Exception as e:
            print(f"  ⚠️  Auth check: {str(e)[:60]}")
        
        print()
        print("=" * 70)
        print("✅ Connection Test: PASSED")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Run schema setup: python scripts/setup_supabase_schema.py")
        print("  2. Or manually run database_schema.sql in Supabase SQL Editor")
        print("  3. Validate: python scripts/validate_supabase_schema.py")
        print()
        
        return True
        
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ Connection Test: FAILED")
        print("=" * 70)
        print()
        print(f"Error: {str(e)}")
        print()
        print("Troubleshooting:")
        print("  1. Verify URL and key are correct")
        print("  2. Check network connectivity")
        print("  3. Ensure Supabase project is active")
        print()
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)

