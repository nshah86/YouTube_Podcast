# Payment Integration Setup Guide

## Overview

VideoTranscript Pro uses Stripe for payment processing and subscription management. This guide will help you set up payments for production.

## Prerequisites

1. Stripe account (https://stripe.com)
2. Stripe API keys (test and live)
3. Database schema with payment tables (run `database_schema_payments.sql`)

## Step 1: Create Stripe Account and Products

1. Go to https://stripe.com and create an account
2. Navigate to Products in Stripe Dashboard
3. Create products for each plan:
   - **Plus Plan**: $9.99/month (recurring)
   - **Pro Plan**: $24.99/month (recurring)
   - **Enterprise Plan**: Custom pricing (contact sales)

4. Note the **Price IDs** for each product (starts with `price_...`)

## Step 2: Configure Environment Variables

Add to your `.env` file:

```env
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_...  # Test key for development
STRIPE_WEBHOOK_SECRET=whsec_...  # Webhook secret (get from Stripe Dashboard)
STRIPE_SUCCESS_URL=https://yourdomain.com/account?payment=success
STRIPE_CANCEL_URL=https://yourdomain.com/pricing?payment=canceled

# Stripe Price IDs (from Step 1)
STRIPE_PRICE_PLUS=price_xxxxx
STRIPE_PRICE_PRO=price_xxxxx
STRIPE_PRICE_ENTERPRISE=price_xxxxx  # Optional, for enterprise
```

## Step 3: Run Database Schema

Run the payment schema SQL in your Supabase SQL Editor:

```bash
# Run database_schema_payments.sql in Supabase SQL Editor
```

This creates:
- `payments` table - Payment transaction records
- `subscriptions` table - Active subscriptions
- `api_usage` table - API call tracking
- Triggers to update user plans automatically

## Step 4: Set Up Webhooks

1. Go to Stripe Dashboard → Developers → Webhooks
2. Click "Add endpoint"
3. Enter your webhook URL: `https://yourdomain.com/api/payment/webhook`
4. Select events to listen for:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
5. Copy the webhook signing secret to `STRIPE_WEBHOOK_SECRET` in `.env`

## Step 5: Test Payment Flow

### Test Mode

1. Use Stripe test cards:
   - Success: `4242 4242 4242 4242`
   - Decline: `4000 0000 0000 0002`
   - 3D Secure: `4000 0025 0000 3155`

2. Test the flow:
   - User clicks "Upgrade to Plus" on pricing page
   - Redirects to Stripe Checkout
   - Complete payment with test card
   - Webhook updates user plan in database
   - User redirected back to account page

### Production Mode

1. Switch to live API keys in `.env`
2. Update webhook URL to production domain
3. Test with real payment (small amount)
4. Monitor webhook logs in Stripe Dashboard

## Payment Flow

1. **User clicks upgrade** → Frontend calls `/api/payment/create-checkout`
2. **Backend creates Stripe session** → Returns checkout URL
3. **User completes payment** → Stripe processes payment
4. **Stripe sends webhook** → `/api/payment/webhook` receives event
5. **Backend updates database**:
   - Creates subscription record
   - Updates user plan
   - Updates token limits
   - Records payment transaction

## Database Tables

### payments
- Records all payment transactions
- Links to Stripe payment intents
- Tracks payment status

### subscriptions
- Active user subscriptions
- Links to Stripe subscription IDs
- Tracks subscription status and periods

### api_usage
- Tracks all API calls
- Records endpoint, method, status, tokens used
- Used for analytics and security

## Security Considerations

1. **Webhook Verification**: Always verify webhook signatures
2. **Idempotency**: Handle duplicate webhook events
3. **Error Handling**: Log all payment errors
4. **Rate Limiting**: Protect payment endpoints
5. **HTTPS**: Always use HTTPS in production

## Monitoring

Monitor these in production:
- Webhook delivery success rate
- Payment success/failure rates
- Subscription cancellations
- API usage patterns

## Troubleshooting

### Webhooks not working
- Check webhook URL is accessible
- Verify webhook secret matches
- Check Stripe webhook logs
- Ensure database schema is applied

### Payments not updating plans
- Check webhook event types
- Verify database triggers are active
- Check application logs
- Verify user profile updates

### API tracking not working
- Ensure `api_usage` table exists
- Check API token IDs are valid
- Verify database connection
- Check application logs

## Support

For payment issues:
1. Check Stripe Dashboard logs
2. Review application logs
3. Check database for records
4. Contact Stripe support if needed

