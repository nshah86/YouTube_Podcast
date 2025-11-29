/*
  # Create Payment and Subscription Schema for VideoTranscript Pro

  1. New Tables
    - `payments`
      - `id` (uuid, primary key)
      - `user_id` (uuid, references user_profiles)
      - `stripe_payment_intent_id` (text, unique)
      - `stripe_customer_id` (text)
      - `stripe_subscription_id` (text)
      - `amount` (integer, cents)
      - `currency` (text, default 'usd')
      - `plan` (text)
      - `status` (text)
      - `payment_method` (text)
      - `created_at` (timestamptz)
      - `updated_at` (timestamptz)
    
    - `subscriptions`
      - `id` (uuid, primary key)
      - `user_id` (uuid, references user_profiles)
      - `stripe_subscription_id` (text, unique)
      - `stripe_customer_id` (text)
      - `plan` (text)
      - `status` (text)
      - `current_period_start` (timestamptz)
      - `current_period_end` (timestamptz)
      - `cancel_at_period_end` (boolean)
      - `canceled_at` (timestamptz)
      - `created_at` (timestamptz)
      - `updated_at` (timestamptz)
    
    - `api_usage`
      - `id` (uuid, primary key)
      - `api_token_id` (uuid, references api_tokens)
      - `user_id` (uuid, references user_profiles)
      - `endpoint` (text)
      - `method` (text)
      - `status_code` (integer)
      - `tokens_used` (integer, default 1)
      - `response_time_ms` (integer)
      - `ip_address` (text)
      - `user_agent` (text)
      - `created_at` (timestamptz)

  2. Schema Updates
    - Add subscription_id, stripe_customer_id, and payment_status to user_profiles

  3. Security
    - Enable RLS on all new tables
    - Users can only view their own payment and subscription data
    - Service role can manage all records (for webhooks)

  4. Functions & Triggers
    - `update_user_plan_from_subscription()` - Updates user plan when subscription changes
    - `update_token_last_used()` - Updates API token last_used_at on API usage
    - Triggers on subscription and api_usage tables

  5. Indexes
    - Performance indexes on foreign keys and lookup columns
    - Indexes for Stripe ID lookups
    - Indexes for usage analytics
*/

-- Payment transactions table
CREATE TABLE IF NOT EXISTS public.payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    stripe_payment_intent_id TEXT UNIQUE,
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    amount INTEGER NOT NULL,
    currency TEXT DEFAULT 'usd',
    plan TEXT NOT NULL CHECK (plan IN ('free', 'plus', 'pro', 'enterprise')),
    status TEXT NOT NULL CHECK (status IN ('pending', 'succeeded', 'failed', 'refunded', 'canceled')),
    payment_method TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Subscriptions table
CREATE TABLE IF NOT EXISTS public.subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    stripe_subscription_id TEXT UNIQUE,
    stripe_customer_id TEXT,
    plan TEXT NOT NULL CHECK (plan IN ('free', 'plus', 'pro', 'enterprise')),
    status TEXT NOT NULL CHECK (status IN ('active', 'canceled', 'past_due', 'unpaid', 'trialing')),
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    canceled_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API usage tracking per token
CREATE TABLE IF NOT EXISTS public.api_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    api_token_id UUID NOT NULL REFERENCES public.api_tokens(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    status_code INTEGER,
    tokens_used INTEGER DEFAULT 1,
    response_time_ms INTEGER,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON public.payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_stripe_payment_intent_id ON public.payments(stripe_payment_intent_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON public.subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_subscription_id ON public.subscriptions(stripe_subscription_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON public.subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_api_usage_token_id ON public.api_usage(api_token_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_user_id ON public.api_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_created_at ON public.api_usage(created_at);

-- Add subscription_id to user_profiles
ALTER TABLE public.user_profiles 
ADD COLUMN IF NOT EXISTS subscription_id UUID REFERENCES public.subscriptions(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT,
ADD COLUMN IF NOT EXISTS payment_status TEXT DEFAULT 'active';

-- Function to update user plan when subscription changes
CREATE OR REPLACE FUNCTION public.update_user_plan_from_subscription()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE public.user_profiles
    SET 
        plan = NEW.plan,
        tokens_limit = CASE 
            WHEN NEW.plan = 'free' THEN 25
            WHEN NEW.plan = 'plus' THEN 1000
            WHEN NEW.plan = 'pro' THEN 3000
            WHEN NEW.plan = 'enterprise' THEN 10000
            ELSE 25
        END,
        subscription_id = NEW.id,
        updated_at = NOW()
    WHERE id = NEW.user_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to update user plan when subscription is created/updated
DROP TRIGGER IF EXISTS on_subscription_created ON public.subscriptions;
CREATE TRIGGER on_subscription_created
    AFTER INSERT OR UPDATE ON public.subscriptions
    FOR EACH ROW
    WHEN (NEW.status = 'active')
    EXECUTE FUNCTION public.update_user_plan_from_subscription();

-- Function to update API token last_used_at
CREATE OR REPLACE FUNCTION public.update_token_last_used()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE public.api_tokens
    SET last_used_at = NOW()
    WHERE id = NEW.api_token_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to update token last_used_at when API is used
DROP TRIGGER IF EXISTS on_api_usage_created ON public.api_usage;
CREATE TRIGGER on_api_usage_created
    AFTER INSERT ON public.api_usage
    FOR EACH ROW
    EXECUTE FUNCTION public.update_token_last_used();

-- Row Level Security (RLS) Policies
ALTER TABLE public.payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_usage ENABLE ROW LEVEL SECURITY;

-- Users can view their own payments
DROP POLICY IF EXISTS "Users can view own payments" ON public.payments;
CREATE POLICY "Users can view own payments"
    ON public.payments
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

-- Users can view their own subscriptions
DROP POLICY IF EXISTS "Users can view own subscriptions" ON public.subscriptions;
CREATE POLICY "Users can view own subscriptions"
    ON public.subscriptions
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

-- Users can view their own API usage
DROP POLICY IF EXISTS "Users can view own API usage" ON public.api_usage;
CREATE POLICY "Users can view own API usage"
    ON public.api_usage
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);