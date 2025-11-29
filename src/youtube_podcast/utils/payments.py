"""
Payment integration utilities for VideoTranscript Pro using Stripe.
"""
import os
import sys
import logging
from typing import Optional, Dict
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    logging.warning("Stripe not installed. Payment features will be disabled.")

from src.youtube_podcast.utils.supabase_client import get_supabase, is_supabase_configured

logger = logging.getLogger(__name__)

# Initialize Stripe
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

if STRIPE_AVAILABLE and STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY
else:
    stripe = None
    logger.warning("Stripe not configured. Set STRIPE_SECRET_KEY in environment variables.")


def is_stripe_configured() -> bool:
    """Check if Stripe is configured."""
    return STRIPE_AVAILABLE and STRIPE_SECRET_KEY is not None


def create_checkout_session(user_id: str, user_email: str, plan: str, price_id: str) -> Optional[Dict]:
    """
    Create a Stripe checkout session for subscription.
    
    Args:
        user_id: User UUID
        user_email: User email
        plan: Plan name (plus, pro, enterprise)
        price_id: Stripe Price ID for the plan
        
    Returns:
        Dictionary with session URL or None if error
    """
    if not is_stripe_configured():
        return None
    
    try:
        # Get or create Stripe customer
        customer_id = get_or_create_stripe_customer(user_id, user_email)
        if not customer_id:
            return None
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=os.getenv('STRIPE_SUCCESS_URL', 'http://localhost:5000/account?payment=success'),
            cancel_url=os.getenv('STRIPE_CANCEL_URL', 'http://localhost:5000/pricing?payment=canceled'),
            metadata={
                'user_id': user_id,
                'plan': plan
            }
        )
        
        return {
            'session_id': session.id,
            'url': session.url
        }
    
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        return None


def get_or_create_stripe_customer(user_id: str, user_email: str) -> Optional[str]:
    """
    Get or create a Stripe customer for the user.
    
    Args:
        user_id: User UUID
        user_email: User email
        
    Returns:
        Stripe customer ID or None if error
    """
    if not is_stripe_configured() or not is_supabase_configured():
        return None
    
    try:
        supabase = get_supabase()
        
        # Check if customer already exists
        profile_response = supabase.table('user_profiles').select('stripe_customer_id').eq('id', user_id).execute()
        
        if profile_response.data and profile_response.data[0].get('stripe_customer_id'):
            return profile_response.data[0]['stripe_customer_id']
        
        # Create new Stripe customer
        customer = stripe.Customer.create(
            email=user_email,
            metadata={
                'user_id': user_id
            }
        )
        
        # Save customer ID to database
        supabase.table('user_profiles').update({
            'stripe_customer_id': customer.id,
            'updated_at': datetime.now().isoformat()
        }).eq('id', user_id).execute()
        
        return customer.id
    
    except Exception as e:
        logger.error(f"Error creating Stripe customer: {str(e)}")
        return None


def handle_stripe_webhook(payload: bytes, signature: str) -> bool:
    """
    Handle Stripe webhook events.
    
    Args:
        payload: Raw webhook payload
        signature: Stripe signature header
        
    Returns:
        True if webhook processed successfully
    """
    if not is_stripe_configured() or not STRIPE_WEBHOOK_SECRET:
        logger.error("Stripe webhook secret not configured")
        return False
    
    try:
        event = stripe.Webhook.construct_event(
            payload, signature, STRIPE_WEBHOOK_SECRET
        )
        
        # Handle different event types
        if event['type'] == 'checkout.session.completed':
            handle_checkout_completed(event['data']['object'])
        elif event['type'] == 'customer.subscription.created':
            handle_subscription_created(event['data']['object'])
        elif event['type'] == 'customer.subscription.updated':
            handle_subscription_updated(event['data']['object'])
        elif event['type'] == 'customer.subscription.deleted':
            handle_subscription_deleted(event['data']['object'])
        elif event['type'] == 'invoice.payment_succeeded':
            handle_payment_succeeded(event['data']['object'])
        elif event['type'] == 'invoice.payment_failed':
            handle_payment_failed(event['data']['object'])
        
        return True
    
    except ValueError as e:
        logger.error(f"Invalid payload: {str(e)}")
        return False
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error handling webhook: {str(e)}")
        return False


def handle_checkout_completed(session: Dict):
    """Handle checkout.session.completed event."""
    try:
        user_id = session.get('metadata', {}).get('user_id')
        if not user_id or not is_supabase_configured():
            return
        
        supabase = get_supabase()
        
        # Record payment
        supabase.table('payments').insert({
            'user_id': user_id,
            'stripe_payment_intent_id': session.get('payment_intent'),
            'stripe_customer_id': session.get('customer'),
            'amount': session.get('amount_total', 0),
            'currency': session.get('currency', 'usd'),
            'status': 'succeeded',
            'payment_method': 'card'
        }).execute()
        
    except Exception as e:
        logger.error(f"Error handling checkout completed: {str(e)}")


def handle_subscription_created(subscription: Dict):
    """Handle customer.subscription.created event."""
    try:
        customer_id = subscription.get('customer')
        if not customer_id or not is_supabase_configured():
            return
        
        supabase = get_supabase()
        
        # Find user by Stripe customer ID
        profile_response = supabase.table('user_profiles').select('id').eq('stripe_customer_id', customer_id).execute()
        if not profile_response.data:
            return
        
        user_id = profile_response.data[0]['id']
        
        # Determine plan from price
        plan = 'free'  # Default
        price_id = subscription.get('items', {}).get('data', [{}])[0].get('price', {}).get('id', '')
        
        # Map price IDs to plans (should be configured in environment)
        price_to_plan = {
            os.getenv('STRIPE_PRICE_PLUS', ''): 'plus',
            os.getenv('STRIPE_PRICE_PRO', ''): 'pro',
            os.getenv('STRIPE_PRICE_ENTERPRISE', ''): 'enterprise'
        }
        
        plan = price_to_plan.get(price_id, 'plus')
        
        # Create subscription record
        supabase.table('subscriptions').insert({
            'user_id': user_id,
            'stripe_subscription_id': subscription.get('id'),
            'stripe_customer_id': customer_id,
            'plan': plan,
            'status': subscription.get('status', 'active'),
            'current_period_start': datetime.fromtimestamp(subscription.get('current_period_start', 0)).isoformat(),
            'current_period_end': datetime.fromtimestamp(subscription.get('current_period_end', 0)).isoformat(),
            'cancel_at_period_end': subscription.get('cancel_at_period_end', False)
        }).execute()
        
    except Exception as e:
        logger.error(f"Error handling subscription created: {str(e)}")


def handle_subscription_updated(subscription: Dict):
    """Handle customer.subscription.updated event."""
    try:
        subscription_id = subscription.get('id')
        if not subscription_id or not is_supabase_configured():
            return
        
        supabase = get_supabase()
        
        # Update subscription record
        supabase.table('subscriptions').update({
            'status': subscription.get('status', 'active'),
            'current_period_start': datetime.fromtimestamp(subscription.get('current_period_start', 0)).isoformat(),
            'current_period_end': datetime.fromtimestamp(subscription.get('current_period_end', 0)).isoformat(),
            'cancel_at_period_end': subscription.get('cancel_at_period_end', False),
            'canceled_at': datetime.fromtimestamp(subscription.get('canceled_at', 0)).isoformat() if subscription.get('canceled_at') else None,
            'updated_at': datetime.now().isoformat()
        }).eq('stripe_subscription_id', subscription_id).execute()
        
    except Exception as e:
        logger.error(f"Error handling subscription updated: {str(e)}")


def handle_subscription_deleted(subscription: Dict):
    """Handle customer.subscription.deleted event."""
    try:
        subscription_id = subscription.get('id')
        if not subscription_id or not is_supabase_configured():
            return
        
        supabase = get_supabase()
        
        # Update subscription status
        supabase.table('subscriptions').update({
            'status': 'canceled',
            'canceled_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }).eq('stripe_subscription_id', subscription_id).execute()
        
        # Update user plan to free
        subscription_response = supabase.table('subscriptions').select('user_id').eq('stripe_subscription_id', subscription_id).execute()
        if subscription_response.data:
            user_id = subscription_response.data[0]['user_id']
            supabase.table('user_profiles').update({
                'plan': 'free',
                'tokens_limit': 25,
                'updated_at': datetime.now().isoformat()
            }).eq('id', user_id).execute()
        
    except Exception as e:
        logger.error(f"Error handling subscription deleted: {str(e)}")


def handle_payment_succeeded(invoice: Dict):
    """Handle invoice.payment_succeeded event."""
    try:
        customer_id = invoice.get('customer')
        if not customer_id or not is_supabase_configured():
            return
        
        supabase = get_supabase()
        
        # Record successful payment
        profile_response = supabase.table('user_profiles').select('id').eq('stripe_customer_id', customer_id).execute()
        if profile_response.data:
            user_id = profile_response.data[0]['id']
            
            supabase.table('payments').insert({
                'user_id': user_id,
                'stripe_payment_intent_id': invoice.get('payment_intent'),
                'stripe_customer_id': customer_id,
                'amount': invoice.get('amount_paid', 0),
                'currency': invoice.get('currency', 'usd'),
                'status': 'succeeded',
                'payment_method': 'card'
            }).execute()
        
    except Exception as e:
        logger.error(f"Error handling payment succeeded: {str(e)}")


def handle_payment_failed(invoice: Dict):
    """Handle invoice.payment_failed event."""
    try:
        customer_id = invoice.get('customer')
        if not customer_id or not is_supabase_configured():
            return
        
        supabase = get_supabase()
        
        # Record failed payment
        profile_response = supabase.table('user_profiles').select('id').eq('stripe_customer_id', customer_id).execute()
        if profile_response.data:
            user_id = profile_response.data[0]['id']
            
            supabase.table('payments').insert({
                'user_id': user_id,
                'stripe_payment_intent_id': invoice.get('payment_intent'),
                'stripe_customer_id': customer_id,
                'amount': invoice.get('amount_due', 0),
                'currency': invoice.get('currency', 'usd'),
                'status': 'failed',
                'payment_method': 'card'
            }).execute()
            
            # Update subscription status if needed
            subscription_response = supabase.table('subscriptions').select('id').eq('stripe_customer_id', customer_id).eq('status', 'active').execute()
            if subscription_response.data:
                supabase.table('subscriptions').update({
                    'status': 'past_due',
                    'updated_at': datetime.now().isoformat()
                }).eq('stripe_customer_id', customer_id).execute()
        
    except Exception as e:
        logger.error(f"Error handling payment failed: {str(e)}")

