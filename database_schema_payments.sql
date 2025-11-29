-- Payment and Subscription Tables for VideoTranscript Pro
-- Run this SQL in your Supabase SQL Editor AFTER running database_schema.sql

-- Payment transactions table
CREATE TABLE IF NOT EXISTS public.payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    stripe_payment_intent_id TEXT UNIQUE,
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    amount INTEGER NOT NULL, -- Amount in cents
    currency TEXT DEFAULT 'usd',
    plan TEXT NOT NULL CHECK (plan IN ('free', 'plus', 'pro', 'enterprise')),
    status TEXT NOT NULL CHECK (status IN ('pending', 'succeeded', 'failed', 'refunded', 'canceled')),
    payment_method TEXT, -- card, paypal, etc.
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
CREATE POLICY "Users can view own payments"
    ON public.payments
    FOR SELECT
    USING (auth.uid() = user_id);

-- Users can view their own subscriptions
CREATE POLICY "Users can view own subscriptions"
    ON public.subscriptions
    FOR SELECT
    USING (auth.uid() = user_id);

-- Users can view their own API usage
CREATE POLICY "Users can view own API usage"
    ON public.api_usage
    FOR SELECT
    USING (auth.uid() = user_id);

-- Service role can manage all records (for webhooks)
-- Note: This requires service_role key, not anon key

