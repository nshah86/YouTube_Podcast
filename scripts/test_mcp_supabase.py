"""
Test MCP Supabase connection and identify what's required to make it work.
This script tests various MCP operations to diagnose connection issues.
"""
import sys
import os
from datetime import datetime

print("=" * 70)
print("MCP Supabase Connection Diagnostic Test")
print("=" * 70)
print(f"Test Time: {datetime.now().isoformat()}")
print()

# Test results
results = {
    "passed": [],
    "failed": [],
    "timeout": [],
    "partial": []
}

def test_operation(name, operation_func):
    """Test a single MCP operation"""
    print(f"Testing: {name}...", end=" ", flush=True)
    try:
        result = operation_func()
        
        if isinstance(result, dict) and "error" in result:
            error_msg = result.get("error", {}).get("message", str(result.get("error")))
            if "timeout" in error_msg.lower() or "Connection terminated" in error_msg:
                print(f"⏱️  TIMEOUT")
                results["timeout"].append((name, error_msg))
            else:
                print(f"❌ FAILED: {error_msg[:50]}")
                results["failed"].append((name, error_msg))
        else:
            print(f"✅ PASSED")
            results["passed"].append((name, result))
            return result
            
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)[:50]}")
        results["failed"].append((name, str(e)))
    
    return None

# Test 1: Get Project URL
print("\n1. Basic Connection Tests")
print("-" * 70)
project_url = test_operation("Get Project URL", lambda: __import__('mcp_supabase_get_project_url').mcp_supabase_get_project_url())

# Test 2: Get Anon Key
anon_key_result = test_operation("Get Anon Key", lambda: __import__('mcp_supabase_get_anon_key').mcp_supabase_get_anon_key())

# Test 3: List Extensions
print("\n2. Database Query Tests")
print("-" * 70)
test_operation("List Extensions", lambda: __import__('mcp_supabase_list_extensions').mcp_supabase_list_extensions())

# Test 4: Simple SQL Query
test_operation("Simple SQL (SELECT version())", lambda: __import__('mcp_supabase_execute_sql').mcp_supabase_execute_sql(query="SELECT version();"))

# Test 5: List Tables
test_operation("List Tables", lambda: __import__('mcp_supabase_list_tables').mcp_supabase_list_tables(schemas=['public']))

# Test 6: List Migrations
test_operation("List Migrations", lambda: __import__('mcp_supabase_list_migrations').mcp_supabase_list_migrations())

# Test 7: Get Logs
print("\n3. Service Tests")
print("-" * 70)
logs_result = test_operation("Get API Logs", lambda: __import__('mcp_supabase_get_logs').mcp_supabase_get_logs(service="api"))

# Test 8: Get Advisors
test_operation("Get Security Advisors", lambda: __import__('mcp_supabase_get_advisors').mcp_supabase_get_advisors(type="security"))

# Summary
print("\n" + "=" * 70)
print("Test Summary")
print("=" * 70)
print(f"✅ Passed: {len(results['passed'])}")
print(f"❌ Failed: {len(results['failed'])}")
print(f"⏱️  Timeout: {len(results['timeout'])}")
print()

if results['passed']:
    print("Working Operations:")
    for name, result in results['passed']:
        print(f"  ✓ {name}")
        if name == "Get Project URL" and isinstance(result, str):
            print(f"    → {result}")
        elif name == "Get API Logs" and isinstance(result, dict):
            log_count = len(result.get('result', []))
            print(f"    → Retrieved {log_count} log entries")
    print()

if results['timeout']:
    print("Timeout Operations (Connection Issues):")
    for name, error in results['timeout']:
        print(f"  ⏱️  {name}")
        print(f"     Error: {error[:80]}")
    print()

if results['failed']:
    print("Failed Operations:")
    for name, error in results['failed']:
        print(f"  ❌ {name}")
        print(f"     Error: {error[:80]}")
    print()

# Diagnosis
print("=" * 70)
print("Diagnosis & Recommendations")
print("=" * 70)
print()

if project_url:
    print(f"✓ MCP Connection: Working")
    print(f"  Project URL: {project_url}")
    print()
else:
    print("❌ MCP Connection: Failed")
    print("  Cannot retrieve project URL")
    print()

if len(results['timeout']) > 0:
    print("⚠️  SQL Operations: Timing Out")
    print("   Possible causes:")
    print("   1. Network/firewall blocking database connections")
    print("   2. Database connection pool exhausted")
    print("   3. MCP server needs authentication/authorization")
    print("   4. Project may need to be activated or configured")
    print()
    print("   Solutions:")
    print("   1. Check Supabase project is active in dashboard")
    print("   2. Verify MCP server has proper permissions")
    print("   3. Try direct SQL execution in Supabase SQL Editor")
    print("   4. Use manual schema setup (see docs/SUPABASE_MCP_SETUP.md)")
    print()

if anon_key_result and isinstance(anon_key_result, dict) and "error" in anon_key_result:
    print("⚠️  Service Details: Cannot Fetch")
    print("   This may indicate:")
    print("   - MCP server needs service role key")
    print("   - Project configuration incomplete")
    print("   - Authentication/authorization issue")
    print()

if logs_result and isinstance(logs_result, dict) and "result" in logs_result:
    print("✓ Logs API: Working")
    print("   Can retrieve service logs via MCP")
    print()

print("=" * 70)
print("Recommended Next Steps")
print("=" * 70)
print()
print("1. For Schema Setup:")
print("   → Use manual method: Run database_schema.sql in Supabase SQL Editor")
print()
print("2. For Validation:")
print("   → Use direct Supabase client: python scripts/validate_supabase_schema.py")
print()
print("3. For Testing:")
print("   → Run automation tests: python run_tests.py")
print()
print("4. To Fix MCP Connection:")
print("   → Check MCP server configuration")
print("   → Verify project_ref in MCP URL matches your project")
print("   → Ensure MCP server has database access permissions")
print()

