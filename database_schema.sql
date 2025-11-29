-- Supabase Database Schema for VideoTranscript Pro
-- Run this SQL in your Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    plan TEXT NOT NULL DEFAULT 'free' CHECK (plan IN ('free', 'plus', 'pro', 'enterprise')),
    tokens_used INTEGER DEFAULT 0,
    tokens_limit INTEGER DEFAULT 25,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API Tokens table
CREATE TABLE IF NOT EXISTS public.api_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    token TEXT UNIQUE NOT NULL,
    name TEXT,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, token)
);

-- Usage history table
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

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_api_tokens_user_id ON public.api_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_api_tokens_token ON public.api_tokens(token);
CREATE INDEX IF NOT EXISTS idx_usage_history_user_id ON public.usage_history(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_history_created_at ON public.usage_history(created_at);

-- Function to automatically create user profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (id, email, plan, tokens_limit)
    VALUES (
        NEW.id,
        NEW.email,
        'free',
        25
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create profile when user signs up
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- Row Level Security (RLS) Policies
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usage_history ENABLE ROW LEVEL SECURITY;

-- Users can read their own profile
CREATE POLICY "Users can view own profile"
    ON public.user_profiles
    FOR SELECT
    USING (auth.uid() = id);

-- Users can update their own profile
CREATE POLICY "Users can update own profile"
    ON public.user_profiles
    FOR UPDATE
    USING (auth.uid() = id);

-- Users can manage their own API tokens
CREATE POLICY "Users can view own tokens"
    ON public.api_tokens
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create own tokens"
    ON public.api_tokens
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own tokens"
    ON public.api_tokens
    FOR DELETE
    USING (auth.uid() = user_id);

-- Users can view their own usage history
CREATE POLICY "Users can view own usage"
    ON public.usage_history
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create own usage records"
    ON public.usage_history
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Function to reset monthly token usage (run via cron or scheduled job)
CREATE OR REPLACE FUNCTION public.reset_monthly_tokens()
RETURNS void AS $$
BEGIN
    UPDATE public.user_profiles
    SET tokens_used = 0,
        updated_at = NOW()
    WHERE tokens_used > 0;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

