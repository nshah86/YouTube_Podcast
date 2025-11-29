/*
  # Fix RLS Policies and Security Issues

  1. Performance Optimization
    - Replace auth.uid() with (select auth.uid()) in all RLS policies
    - This prevents re-evaluation for each row and improves query performance
    
  2. Function Security
    - Add SECURITY DEFINER and set search_path for functions
    - Prevents SQL injection and improves security
    
  3. Tables Updated
    - user_profiles
    - api_tokens
    - usage_history
    - profiles
    - transcripts
    - podcasts
    
  Note: Indexes marked as unused are kept for future query optimization
*/

-- Drop existing policies to recreate them with optimized syntax
-- user_profiles table
DROP POLICY IF EXISTS "Users can view own profile" ON user_profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON user_profiles;

CREATE POLICY "Users can view own profile"
  ON user_profiles FOR SELECT
  TO authenticated
  USING (id = (select auth.uid()));

CREATE POLICY "Users can update own profile"
  ON user_profiles FOR UPDATE
  TO authenticated
  USING (id = (select auth.uid()))
  WITH CHECK (id = (select auth.uid()));

-- api_tokens table
DROP POLICY IF EXISTS "Users can view own tokens" ON api_tokens;
DROP POLICY IF EXISTS "Users can create own tokens" ON api_tokens;
DROP POLICY IF EXISTS "Users can delete own tokens" ON api_tokens;

CREATE POLICY "Users can view own tokens"
  ON api_tokens FOR SELECT
  TO authenticated
  USING (user_id = (select auth.uid()));

CREATE POLICY "Users can create own tokens"
  ON api_tokens FOR INSERT
  TO authenticated
  WITH CHECK (user_id = (select auth.uid()));

CREATE POLICY "Users can delete own tokens"
  ON api_tokens FOR DELETE
  TO authenticated
  USING (user_id = (select auth.uid()));

-- usage_history table
DROP POLICY IF EXISTS "Users can view own usage" ON usage_history;
DROP POLICY IF EXISTS "Users can create own usage records" ON usage_history;

CREATE POLICY "Users can view own usage"
  ON usage_history FOR SELECT
  TO authenticated
  USING (user_id = (select auth.uid()));

CREATE POLICY "Users can create own usage records"
  ON usage_history FOR INSERT
  TO authenticated
  WITH CHECK (user_id = (select auth.uid()));

-- profiles table
DROP POLICY IF EXISTS "Users can view own profile" ON profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON profiles;

CREATE POLICY "Users can view own profile"
  ON profiles FOR SELECT
  TO authenticated
  USING (id = (select auth.uid()));

CREATE POLICY "Users can update own profile"
  ON profiles FOR UPDATE
  TO authenticated
  USING (id = (select auth.uid()))
  WITH CHECK (id = (select auth.uid()));

-- transcripts table
DROP POLICY IF EXISTS "Users can view own transcripts" ON transcripts;
DROP POLICY IF EXISTS "Users can insert own transcripts" ON transcripts;
DROP POLICY IF EXISTS "Users can delete own transcripts" ON transcripts;

CREATE POLICY "Users can view own transcripts"
  ON transcripts FOR SELECT
  TO authenticated
  USING (user_id = (select auth.uid()));

CREATE POLICY "Users can insert own transcripts"
  ON transcripts FOR INSERT
  TO authenticated
  WITH CHECK (user_id = (select auth.uid()));

CREATE POLICY "Users can delete own transcripts"
  ON transcripts FOR DELETE
  TO authenticated
  USING (user_id = (select auth.uid()));

-- podcasts table
DROP POLICY IF EXISTS "Users can view own podcasts" ON podcasts;
DROP POLICY IF EXISTS "Users can insert own podcasts" ON podcasts;
DROP POLICY IF EXISTS "Users can update own podcasts" ON podcasts;
DROP POLICY IF EXISTS "Users can delete own podcasts" ON podcasts;

CREATE POLICY "Users can view own podcasts"
  ON podcasts FOR SELECT
  TO authenticated
  USING (user_id = (select auth.uid()));

CREATE POLICY "Users can insert own podcasts"
  ON podcasts FOR INSERT
  TO authenticated
  WITH CHECK (user_id = (select auth.uid()));

CREATE POLICY "Users can update own podcasts"
  ON podcasts FOR UPDATE
  TO authenticated
  USING (user_id = (select auth.uid()))
  WITH CHECK (user_id = (select auth.uid()));

CREATE POLICY "Users can delete own podcasts"
  ON podcasts FOR DELETE
  TO authenticated
  USING (user_id = (select auth.uid()));

-- Fix function security issues
-- Drop and recreate handle_new_user function with proper security
DROP FUNCTION IF EXISTS handle_new_user() CASCADE;

CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER
SECURITY DEFINER
SET search_path = public, auth
LANGUAGE plpgsql
AS $$
BEGIN
  INSERT INTO public.user_profiles (id, email, plan, tokens_used, tokens_limit)
  VALUES (
    NEW.id,
    NEW.email,
    'free',
    0,
    25
  );
  RETURN NEW;
EXCEPTION
  WHEN unique_violation THEN
    RETURN NEW;
  WHEN OTHERS THEN
    RAISE LOG 'Error in handle_new_user: %', SQLERRM;
    RETURN NEW;
END;
$$;

-- Recreate trigger if it exists
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION handle_new_user();

-- Fix reset_monthly_tokens function with proper security
DROP FUNCTION IF EXISTS reset_monthly_tokens();

CREATE OR REPLACE FUNCTION reset_monthly_tokens()
RETURNS void
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE user_profiles
  SET 
    tokens_used = 0,
    updated_at = now()
  WHERE updated_at < date_trunc('month', now());
END;
$$;

-- Add comment explaining indexes are for future optimization
COMMENT ON INDEX idx_transcripts_user_id IS 'Index for user transcript queries - will be used as data grows';
COMMENT ON INDEX idx_transcripts_video_id IS 'Index for video lookup queries - will be used as data grows';
COMMENT ON INDEX idx_podcasts_user_id IS 'Index for user podcast queries - will be used as data grows';
COMMENT ON INDEX idx_podcasts_transcript_id IS 'Index for transcript-podcast joins - will be used as data grows';
COMMENT ON INDEX idx_api_tokens_user_id IS 'Index for user token queries - will be used as data grows';
COMMENT ON INDEX idx_api_tokens_token IS 'Index for token authentication - will be used as data grows';
COMMENT ON INDEX idx_usage_history_user_id IS 'Index for user usage queries - will be used as data grows';
COMMENT ON INDEX idx_usage_history_created_at IS 'Index for temporal queries - will be used as data grows';
