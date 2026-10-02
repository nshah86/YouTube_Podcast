"""
Stripe billing for VideoTranscript Pro.

Plan hierarchy: free < plus < pro < enterprise

- Basic transcript extraction (/extract) stays free.
- AI features (summaries, podcast generation, bulk processing, CSV import,
  playlist extraction, API) require an active paid plan.
- All Stripe price IDs come from environment variables -- never hardcode them.
"""
import os
from functools import wraps

from flask import jsonify, request, session

try:
    import stripe

    STRIPE_AVAILABLE = True
except ImportError:  # pragma: no cover - handled gracefully at runtime
    stripe = None
    STRIPE_AVAILABLE = False


# plan -> tier config. Stripe Price IDs are resolved from env vars so the
# same code works across Stripe test/live modes without edits.
PLAN_TIERS = {
    "plus": {
        "name": "Plus",
        "monthly_price_usd": 9,
        "price_env_var": "STRIPE_PRICE_PLUS_MONTHLY",
        "tokens_limit": 1000,
        "features": [
            "Everything in Free",
            "AI-powered video summaries",
            "Podcast generation (MP3 download)",
            "1,000 API tokens / month",
            "Priority processing",
        ],
    },
    "pro": {
        "name": "Pro",
        "monthly_price_usd": 29,
        "price_env_var": "STRIPE_PRICE_PRO_MONTHLY",
        "tokens_limit": 3000,
        "features": [
            "Everything in Plus",
            "Bulk transcript extraction (up to 50 videos)",
            "CSV import / export",
            "Playlist extraction",
            "Channel API access",
            "3,000 API tokens / month",
        ],
    },
}

# Plans that unlock paid features.
PAID_PLANS = ("plus", "pro", "enterprise")

# Tokens granted when a subscription lapses back to free.
FREE_TOKENS_LIMIT = 25


# ---------------------------------------------------------------------------
# Stripe client helpers
# ---------------------------------------------------------------------------

def _get_stripe():
    """Return the configured stripe module, or raise a clear error."""
    if not STRIPE_AVAILABLE:
        raise RuntimeError(
            "The 'stripe' package is not installed. Run: pip install stripe"
        )
    secret = os.getenv("STRIPE_SECRET_KEY", "")
    if not secret:
        raise RuntimeError("STRIPE_SECRET_KEY is not set in the environment")
    stripe.api_key = secret
    return stripe


def get_price_id(plan: str) -> str:
    """Resolve the Stripe Price ID for a plan from the environment."""
    tier = PLAN_TIERS.get(plan)
    if not tier:
        raise ValueError(f"Unknown plan: {plan!r}")
    price_id = os.getenv(tier["price_env_var"], "")
    if not price_id:
        raise RuntimeError(
            f"{tier['price_env_var']} is not set. Create the price in the "
            "Stripe Dashboard and add its ID to the environment."
        )
    return price_id


def plan_for_price_id(price_id: str):
    """Map a Stripe Price ID back to a plan name (reverse of get_price_id)."""
    for plan, tier in PLAN_TIERS.items():
        if os.getenv(tier["price_env_var"], "") == price_id:
            return plan
    return None


def _service_db():
    """Supabase client with the service-role key (bypasses RLS).

    Webhook handlers run without a user session, so they must use the
    service key. Never expose this client to browser-facing code paths.
    """
    try:
        from supabase import create_client
    except ImportError:
        raise RuntimeError("The 'supabase' package is not installed")
    url = os.getenv("SUPABASE_URL", "")
    service_key = os.getenv("SUPABASE_SERVICE_KEY", "")
    if not url or not service_key:
        raise RuntimeError(
            "SUPABASE_URL / SUPABASE_SERVICE_KEY are required for billing writes"
        )
    return create_client(url, service_key)


# ---------------------------------------------------------------------------
# Checkout + customer portal
# ---------------------------------------------------------------------------

def create_checkout_session(user_id: str, email: str, plan: str) -> str:
    """Create a Stripe Checkout Session for a subscription; return its URL."""
    s = _get_stripe()
    price_id = get_price_id(plan)

    db = _service_db()
    customer_id = None
    try:
        existing = (
            db.table("user_profiles")
            .select("stripe_customer_id")
            .eq("id", user_id)
            .execute()
        )
        if existing.data:
            customer_id = existing.data[0].get("stripe_customer_id")
    except Exception:
        customer_id = None

    base_url = os.getenv("APP_BASE_URL", "").rstrip("/") or request.host_url.rstrip("/")

    kwargs = {
        "mode": "subscription",
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": f"{base_url}/account?billing=success",
        "cancel_url": f"{base_url}/pricing?billing=cancelled",
        "metadata": {"user_id": user_id, "plan": plan},
        "subscription_data": {"metadata": {"user_id": user_id, "plan": plan}},
    }
    if customer_id:
        kwargs["customer"] = customer_id
    else:
        kwargs["customer_email"] = email

    checkout = s.checkout.Session.create(**kwargs)
    return checkout.url


def create_portal_session(user_id: str) -> str:
    """Create a Stripe Billing Portal session; return its URL."""
    s = _get_stripe()
    db = _service_db()
    resp = (
        db.table("user_profiles")
        .select("stripe_customer_id")
        .eq("id", user_id)
        .execute()
    )
    customer_id = resp.data[0].get("stripe_customer_id") if resp.data else None
    if not customer_id:
        raise RuntimeError("No Stripe customer found for this account yet")

    base_url = os.getenv("APP_BASE_URL", "").rstrip("/") or request.host_url.rstrip("/")
    portal = s.billing_portal.Session.create(
        customer=customer_id,
        return_url=f"{base_url}/account",
    )
    return portal.url


def get_user_plan(user_id: str) -> str:
    """Return the user's current plan from user_profiles (defaults to free)."""
    db = _service_db()
    resp = db.table("user_profiles").select("plan").eq("id", user_id).execute()
    if resp.data:
        return resp.data[0].get("plan") or "free"
    return "free"


# ---------------------------------------------------------------------------
# Webhook handling
# ---------------------------------------------------------------------------

def handle_webhook(payload: bytes, sig_header: str):
    """Verify and process a Stripe webhook. Returns (status_code, body)."""
    s = _get_stripe()
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if not webhook_secret:
        return 500, {"error": "STRIPE_WEBHOOK_SECRET is not configured"}

    try:
        event = s.Webhook.construct_event(payload, sig_header, webhook_secret)
    except Exception as exc:  # signature mismatch, bad payload, etc.
        return 400, {"error": f"Webhook signature verification failed: {exc}"}

    event_type = event.get("type", "")
    data_object = event.get("data", {}).get("object", {})

    try:
        if event_type == "checkout.session.completed":
            _on_checkout_completed(data_object)
        elif event_type == "customer.subscription.updated":
            _on_subscription_updated(data_object)
        elif event_type == "customer.subscription.deleted":
            _on_subscription_deleted(data_object)
        # Other event types are acknowledged but ignored.
    except Exception as exc:
        return 500, {"error": f"Webhook handler failed: {exc}"}

    return 200, {"received": True, "type": event_type}


def _activate_subscription(user_id, customer_id, subscription_id, plan,
                           status, period_start, period_end):
    """Write the subscription state to user_profiles + subscriptions."""
    db = _service_db()
    tokens_limit = PLAN_TIERS.get(plan, {}).get("tokens_limit", FREE_TOKENS_LIMIT)

    db.table("user_profiles").update(
        {
            "plan": plan,
            "tokens_limit": tokens_limit,
            "stripe_customer_id": customer_id,
        }
    ).eq("id", user_id).execute()

    # Upsert into subscriptions (match on stripe_subscription_id when present).
    row = {
        "user_id": user_id,
        "stripe_subscription_id": subscription_id,
        "stripe_customer_id": customer_id,
        "plan": plan,
        "status": status,
        "current_period_start": _ts(period_start),
        "current_period_end": _ts(period_end),
    }
    if subscription_id:
        existing = (
            db.table("subscriptions")
            .select("id")
            .eq("stripe_subscription_id", subscription_id)
            .execute()
        )
        if existing.data:
            db.table("subscriptions").update(row).eq(
                "stripe_subscription_id", subscription_id
            ).execute()
        else:
            db.table("subscriptions").insert(row).execute()
    else:
        db.table("subscriptions").insert(row).execute()


def _ts(epoch_seconds):
    """Convert Stripe epoch seconds to ISO-8601 (or None)."""
    if not epoch_seconds:
        return None
    from datetime import datetime, timezone

    return datetime.fromtimestamp(epoch_seconds, tz=timezone.utc).isoformat()


def _on_checkout_completed(session_obj):
    metadata = session_obj.get("metadata", {}) or {}
    user_id = metadata.get("user_id")
    plan = metadata.get("plan")
    if not user_id or not plan:
        raise ValueError("checkout.session.completed is missing user_id/plan metadata")

    customer_id = session_obj.get("customer")
    subscription_id = session_obj.get("subscription")

    status = "active"
    period_start = period_end = None
    if subscription_id:
        s = _get_stripe()
        sub = s.Subscription.retrieve(subscription_id)
        status = sub.get("status", "active")
        period_start = sub.get("current_period_start")
        period_end = sub.get("current_period_end")
        items = (sub.get("items", {}) or {}).get("data", [])
        if items:
            detected = plan_for_price_id(items[0].get("price", {}).get("id", ""))
            if detected:
                plan = detected

    _activate_subscription(user_id, customer_id, subscription_id, plan,
                           status, period_start, period_end)

    # Record the first payment.
    db = _service_db()
    db.table("payments").insert(
        {
            "user_id": user_id,
            "stripe_invoice_id": session_obj.get("invoice"),
            "stripe_subscription_id": subscription_id,
            "amount": session_obj.get("amount_total"),
            "currency": session_obj.get("currency") or "usd",
            "status": "succeeded",
            "plan": plan,
        }
    ).execute()


def _find_user_by_customer(customer_id):
    db = _service_db()
    resp = (
        db.table("user_profiles")
        .select("id")
        .eq("stripe_customer_id", customer_id)
        .execute()
    )
    return resp.data[0]["id"] if resp.data else None


def _on_subscription_updated(sub):
    customer_id = sub.get("customer")
    user_id = _find_user_by_customer(customer_id)
    if not user_id:
        return  # unknown customer; nothing to do

    items = (sub.get("items", {}) or {}).get("data", [])
    plan = plan_for_price_id(items[0].get("price", {}).get("id", "")) if items else None
    if not plan:
        # Keep the existing plan; just sync status/period.
        plan = get_user_plan(user_id)

    _activate_subscription(
        user_id,
        customer_id,
        sub.get("id"),
        plan,
        sub.get("status", "active"),
        sub.get("current_period_start"),
        sub.get("current_period_end"),
    )


def _on_subscription_deleted(sub):
    customer_id = sub.get("customer")
    user_id = _find_user_by_customer(customer_id)
    if not user_id:
        return

    db = _service_db()
    db.table("user_profiles").update(
        {"plan": "free", "tokens_limit": FREE_TOKENS_LIMIT}
    ).eq("id", user_id).execute()

    if sub.get("id"):
        db.table("subscriptions").update({"status": "canceled"}).eq(
            "stripe_subscription_id", sub.get("id")
        ).execute()


# ---------------------------------------------------------------------------
# Access control for the web UI (Flask session users)
# ---------------------------------------------------------------------------

def requires_paid_plan(view):
    """Require an active paid plan (plus/pro/enterprise) for a web route.

    Basic transcript extraction stays free; AI features do not.
    """
    @wraps(view)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        try:
            plan = get_user_plan(user_id)
        except Exception as exc:
            return jsonify({"error": f"Could not verify subscription: {exc}"}), 503
        if plan not in PAID_PLANS:
            return (
                jsonify(
                    {
                        "error": "This feature requires a paid plan",
                        "current_plan": plan,
                        "upgrade_url": "/pricing",
                    }
                ),
                402,
            )
        return view(*args, **kwargs)

    return wrapper
