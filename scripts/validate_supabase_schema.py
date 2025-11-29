"""
Validate Supabase schema setup using MCP or direct connection.
Run this script to verify database schema is correctly configured.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

try:
    from src.youtube_podcast.utils.supabase_client import get_supabase, is_supabase_configured
    HAS_SUPABASE_CLIENT = True
except ImportError:
    HAS_SUPABASE_CLIENT = False


def validate_schema_mcp():
    """Validate schema using MCP Supabase connection"""
    try:
        # Try to use MCP Supabase tools
        from mcp_supabase_list_tables import mcp_supabase_list_tables
        
        print("🔗 Using MCP Supabase connection...")
        result = mcp_supabase_list_tables(schemas=['public'])
        
        if 'error' in result:
            print(f"⚠️  MCP connection error: {result['error']}")
            return False
        
        tables = result.get('tables', [])
        required_tables = ['user_profiles', 'api_tokens', 'usage_history']
        
        found_tables = [t['name'] for t in tables if isinstance(t, dict) and 'name' in t]
        
        all_found = True
        for table in required_tables:
            if table in found_tables:
                print(f"✓ Table '{table}' exists")
            else:
                print(f"❌ Table '{table}' not found")
                all_found = False
        
        return all_found
        
    except ImportError:
        print("⚠️  MCP Supabase tools not available")
        return False
    except Exception as e:
        print(f"⚠️  MCP validation error: {str(e)}")
        return False


def validate_schema_direct():
    """Validate schema using direct Supabase client"""
    if not HAS_SUPABASE_CLIENT:
        print("❌ Supabase client not available")
        return False
    
    if not is_supabase_configured():
        print("❌ Supabase not configured!")
        print("   Please set REACT_APP_SUPABASE_URL and REACT_APP_SUPABASE_ANON_KEY in .env")
        return False
    
    print("✓ Supabase client initialized")
    print()
    
    supabase = get_supabase()
    required_tables = ['user_profiles', 'api_tokens', 'usage_history']
    
    all_valid = True
    
    for table in required_tables:
        try:
            # Try to query the table
            response = supabase.table(table).select('*').limit(1).execute()
            print(f"✓ Table '{table}' exists and is accessible")
        except Exception as e:
            print(f"❌ Table '{table}' error: {str(e)}")
            all_valid = False
    
    return all_valid


def validate_schema():
    """Validate that all required tables exist in Supabase"""
    print("=" * 60)
    print("Supabase Schema Validation")
    print("=" * 60)
    print()
    
    # Try MCP first, then fall back to direct connection
    print("Attempting validation methods...")
    print()
    
    # Try MCP
    mcp_valid = validate_schema_mcp()
    
    if mcp_valid:
        print()
        print("✅ All tables validated successfully via MCP!")
        return True
    
    # Fall back to direct connection
    print()
    print("Falling back to direct Supabase connection...")
    print()
    
    direct_valid = validate_schema_direct()
    
    print()
    
    if direct_valid:
        print("✅ All tables validated successfully!")
        print()
        print("Next steps:")
        print("  1. Verify RLS policies are enabled")
        print("  2. Test user creation with: python -m pytest tests/test_automation.py::TestAutomation::test_02_user_signup -v")
        return True
    else:
        print("❌ Schema validation failed!")
        print()
        print("Please ensure:")
        print("  1. Supabase MCP is configured or")
        print("  2. Run database_schema.sql in your Supabase SQL Editor:")
        print("     - Go to Supabase Dashboard > SQL Editor")
        print("     - Copy contents of database_schema.sql")
        print("     - Run the SQL script")
        print("  3. Set REACT_APP_SUPABASE_URL and REACT_APP_SUPABASE_ANON_KEY in .env")
        print("  4. Run this validation again")
        return False


if __name__ == "__main__":
    success = validate_schema()
    sys.exit(0 if success else 1)
