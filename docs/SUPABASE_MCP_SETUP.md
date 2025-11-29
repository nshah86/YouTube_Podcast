# Supabase MCP Setup Guide

## MCP Configuration

The Supabase MCP server is configured with:
- **Project Reference**: `dostficclwnmxkiqstix`
- **MCP URL**: `https://mcp.supabase.com/mcp?project_ref=dostficclwnmxkiqstix`

## Schema Setup

### Option 1: Manual Setup (Recommended if MCP times out)

1. **Go to Supabase Dashboard**
   - Visit: https://supabase.com/dashboard
   - Select your project

2. **Open SQL Editor**
   - Navigate to: SQL Editor in the left sidebar

3. **Run Schema Script**
   - Open `database_schema.sql` from the project root
   - Copy all SQL content
   - Paste into SQL Editor
   - Click "Run" to execute

4. **Verify Schema**
   ```bash
   python scripts/validate_supabase_schema.py
   ```

### Option 2: Using Setup Script

```bash
python scripts/setup_supabase_schema.py
```

This script will attempt MCP connection and provide manual instructions if it fails.

## Validation

After setting up the schema, validate it:

```bash
python scripts/validate_supabase_schema.py
```

This script will:
- Try MCP connection first
- Fall back to direct Supabase client connection
- Verify all required tables exist
- Check table accessibility

## Required Tables

The schema creates these tables:

1. **user_profiles** - User account information
2. **api_tokens** - API authentication tokens
3. **usage_history** - User activity tracking

## Testing

After schema is set up, run automation tests:

```bash
# Start Flask app
python start.py

# In another terminal, run tests
python run_tests.py
```

The tests will:
- Create test users via signup
- Test login functionality
- Verify user creation in Supabase
- Test transcript extraction
- Test usage tracking

## Troubleshooting

### MCP Connection Timeout

If MCP connection times out:
1. Check network connectivity
2. Verify MCP server URL is correct
3. Use manual setup (Option 1) instead

### Schema Validation Fails

If validation fails:
1. Ensure `.env` has correct Supabase credentials:
   ```
   REACT_APP_SUPABASE_URL=https://your-project.supabase.co
   REACT_APP_SUPABASE_ANON_KEY=your-anon-key
   ```
2. Verify tables were created in Supabase Dashboard
3. Check RLS policies are enabled

### Tests Fail

If automation tests fail:
1. Ensure Flask app is running
2. Verify Supabase schema is set up
3. Check test user credentials are valid
4. Review test reports in `test_reports/` folder

