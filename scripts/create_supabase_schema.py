"""
Create Supabase schema using direct Python client.
This script executes the database_schema.sql via Supabase client.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from supabase import create_client, Client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False
    print("❌ supabase-py not installed. Run: pip install supabase")
    sys.exit(1)

def create_schema():
    """Create database schema using Supabase client"""
    print("=" * 70)
    print("Creating Supabase Schema")
    print("=" * 70)
    print()
    
    # Get credentials
    supabase_url = os.getenv("REACT_APP_SUPABASE_URL") or os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("REACT_APP_SUPABASE_ANON_KEY") or os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Supabase credentials not found in .env file")
        print("   Please set REACT_APP_SUPABASE_URL and REACT_APP_SUPABASE_ANON_KEY")
        return False
    
    # Create client
    print(f"Connecting to: {supabase_url}")
    supabase: Client = create_client(supabase_url, supabase_key)
    print("✓ Connected")
    print()
    
    # Read schema file
    project_root = Path(__file__).parent.parent
    schema_file = project_root / "database_schema.sql"
    
    if not schema_file.exists():
        print(f"❌ Schema file not found: {schema_file}")
        return False
    
    print(f"Reading schema from: {schema_file}")
    with open(schema_file, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    print("✓ Schema file loaded")
    print()
    
    # Note: Supabase Python client doesn't support direct SQL execution
    # We need to use the REST API or SQL Editor
    print("⚠️  Direct SQL execution not available via Python client")
    print()
    print("The Supabase Python client doesn't support executing arbitrary SQL.")
    print("You need to use one of these methods:")
    print()
    print("Method 1: Supabase Dashboard (Recommended)")
    print("  1. Go to: https://supabase.com/dashboard")
    print("  2. Select your project")
    print("  3. Go to SQL Editor")
    print(f"  4. Copy contents of: {schema_file}")
    print("  5. Paste and click 'Run'")
    print()
    print("Method 2: Supabase CLI")
    print("  1. Install: npm install -g supabase")
    print("  2. Login: supabase login")
    print("  3. Link project: supabase link --project-ref dostficclwnmxkiqstix")
    print(f"  4. Run: supabase db push --file {schema_file}")
    print()
    print("Method 3: Use MCP (if connection works)")
    print("  The MCP server should support apply_migration")
    print()
    
    # Try to validate what we can
    print("=" * 70)
    print("Validating Current Schema")
    print("=" * 70)
    print()
    
    required_tables = ['user_profiles', 'api_tokens', 'usage_history']
    existing_tables = []
    missing_tables = []
    
    for table in required_tables:
        try:
            result = supabase.table(table).select('*').limit(1).execute()
            existing_tables.append(table)
            print(f"✓ Table '{table}' exists")
        except Exception as e:
            error_msg = str(e)
            if "does not exist" in error_msg.lower() or "relation" in error_msg.lower():
                missing_tables.append(table)
                print(f"❌ Table '{table}' does not exist")
            else:
                # Might be RLS or permission issue
                print(f"⚠️  Table '{table}' - {error_msg[:60]}")
    
    print()
    
    if len(existing_tables) == len(required_tables):
        print("✅ All tables exist! Schema is set up correctly.")
        return True
    elif len(missing_tables) > 0:
        print(f"⚠️  {len(missing_tables)} table(s) missing: {', '.join(missing_tables)}")
        print()
        print("Please run the schema setup using one of the methods above.")
        return False
    else:
        print("⚠️  Unable to verify table existence (may be permission issue)")
        return False

if __name__ == "__main__":
    success = create_schema()
    sys.exit(0 if success else 1)

