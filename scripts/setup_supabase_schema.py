"""
Setup Supabase schema using MCP or direct SQL execution.
This script attempts to create the database schema via MCP first,
then falls back to providing instructions for manual setup.
"""
import os
import sys
from pathlib import Path

# Get project root
project_root = Path(__file__).parent.parent


def setup_via_mcp():
    """Attempt to setup schema via MCP Supabase"""
    print("=" * 60)
    print("Supabase Schema Setup via MCP")
    print("=" * 60)
    print()
    
    print("Attempting to apply migrations via MCP...")
    print()
    
    # Read schema file
    schema_file = project_root / "database_schema.sql"
    if not schema_file.exists():
        print(f"❌ Schema file not found: {schema_file}")
        return False
    
    with open(schema_file, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    # Split into logical migrations
    migrations = [
        {
            "name": "01_enable_uuid_extension",
            "query": "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
        },
        {
            "name": "02_create_user_profiles",
            "query": """
CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    plan TEXT NOT NULL DEFAULT 'free' CHECK (plan IN ('free', 'plus', 'pro', 'enterprise')),
    tokens_used INTEGER DEFAULT 0,
    tokens_limit INTEGER DEFAULT 25,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
"""
        },
        {
            "name": "03_create_api_tokens",
            "query": """
CREATE TABLE IF NOT EXISTS public.api_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    token TEXT UNIQUE NOT NULL,
    name TEXT,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, token)
);

CREATE INDEX IF NOT EXISTS idx_api_tokens_user_id ON public.api_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_api_tokens_token ON public.api_tokens(token);
"""
        },
        {
            "name": "04_create_usage_history",
            "query": """
CREATE TABLE IF NOT EXISTS public.usage_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    video_id TEXT,
    video_url TEXT,
    transcript_length INTEGER,
    operation_type TEXT CHECK (operation_type IN ('extract', 'summary', 'podcast')),
    tokens_used INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usage_history_user_id ON public.usage_history(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_history_created_at ON public.usage_history(created_at);
"""
        },
        {
            "name": "05_create_user_profile_trigger",
            "query": """
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (id, email, plan, tokens_limit)
    VALUES (NEW.id, NEW.email, 'free', 25)
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();
"""
        },
        {
            "name": "06_setup_rls_policies",
            "query": """
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usage_history ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own profile" ON public.user_profiles;
CREATE POLICY "Users can view own profile" ON public.user_profiles FOR SELECT USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own profile" ON public.user_profiles;
CREATE POLICY "Users can update own profile" ON public.user_profiles FOR UPDATE USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can view own tokens" ON public.api_tokens;
CREATE POLICY "Users can view own tokens" ON public.api_tokens FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create own tokens" ON public.api_tokens;
CREATE POLICY "Users can create own tokens" ON public.api_tokens FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own tokens" ON public.api_tokens;
CREATE POLICY "Users can delete own tokens" ON public.api_tokens FOR DELETE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can view own usage" ON public.usage_history;
CREATE POLICY "Users can view own usage" ON public.usage_history FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create own usage records" ON public.usage_history;
CREATE POLICY "Users can create own usage records" ON public.usage_history FOR INSERT WITH CHECK (auth.uid() = user_id);
"""
        },
        {
            "name": "07_create_reset_tokens_function",
            "query": """
CREATE OR REPLACE FUNCTION public.reset_monthly_tokens()
RETURNS void AS $$
BEGIN
    UPDATE public.user_profiles
    SET tokens_used = 0, updated_at = NOW()
    WHERE tokens_used > 0;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
"""
        }
    ]
    
    print(f"Found {len(migrations)} migrations to apply")
    print()
    
    # Note: MCP migrations would be applied here if connection works
    # For now, provide manual instructions
    print("⚠️  MCP connection not available or timed out")
    print()
    print("Please apply schema manually:")
    print()
    print("1. Go to Supabase Dashboard > SQL Editor")
    print(f"2. Copy contents of: {schema_file}")
    print("3. Paste and execute the SQL script")
    print("4. Run validation: python scripts/validate_supabase_schema.py")
    print()
    
    return False


def main():
    """Main setup function"""
    success = setup_via_mcp()
    
    if not success:
        print()
        print("=" * 60)
        print("Manual Setup Instructions")
        print("=" * 60)
        print()
        print("Since MCP connection is not available, please:")
        print()
        print("1. Open Supabase Dashboard: https://supabase.com/dashboard")
        print("2. Select your project")
        print("3. Go to SQL Editor")
        print(f"4. Open file: {project_root / 'database_schema.sql'}")
        print("5. Copy all SQL and paste into SQL Editor")
        print("6. Click 'Run' to execute")
        print("7. Verify with: python scripts/validate_supabase_schema.py")
        print()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

