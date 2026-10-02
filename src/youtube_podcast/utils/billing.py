

# ---------------------------------------------------------------------------
# API request quotas (usage-based tier for the public API)
#
# Separate from the AI "token" quotas above: this counts API *requests* per
# calendar month, the standard B2B model for transcript/summary APIs.
# ---------------------------------------------------------------------------

API_REQUEST_QUOTAS = {
    "free": 20,
    "plus": 2000,
    "pro": 50000,
    "enterprise": 50000,
}


def get_api_request_quota(plan: str) -> int:
    """Monthly API request quota for a plan (defaults to free)."""
    return API_REQUEST_QUOTAS.get((plan or "free").lower(), API_REQUEST_QUOTAS["free"])


def _month_start_utc() -> str:
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()


def get_monthly_api_request_count(user_id: str) -> int:
    """Count this user's API requests since the start of the calendar month."""
    try:
        db = _service_db()
    except Exception:
        return 0  # fail open when billing DB is not configured (local dev)
    try:
        resp = (
            db.table("api_usage")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .gte("created_at", _month_start_utc())
            .execute()
        )
        return resp.count or 0
    except Exception:
        return 0


def get_api_quota_remaining(user_id: str) -> dict:
    """Return {plan, limit, used, remaining} for the user's API quota."""
    try:
        plan = get_user_plan(user_id)
    except Exception:
        plan = "free"
    limit = get_api_request_quota(plan)
    used = get_monthly_api_request_count(user_id)
    return {
        "plan": plan,
        "limit": limit,
        "used": used,
        "remaining": max(0, limit - used),
    }


def quota_headers(user_id: str) -> dict:
    """HTTP headers describing the caller's API quota state."""
    q = get_api_quota_remaining(user_id)
    return {
        "X-Quota-Limit": str(q["limit"]),
        "X-Quota-Remaining": str(q["remaining"]),
        "X-Quota-Plan": q["plan"],
    }


def requires_api_quota(view):
    """Enforce the monthly API request quota (429 when exhausted).

    Compose OUTSIDE requires_plan/requires_auth so request.api_user_id
    is already set:

        @requires_api_quota
        @requires_plan('plus')
        def my_endpoint(): ...
    """
    @wraps(view)
    def wrapper(*args, **kwargs):
        user_id = getattr(request, "api_user_id", None)
        if not user_id:
            return view(*args, **kwargs)  # not an API-token call; nothing to enforce
        q = get_api_quota_remaining(user_id)
        if q["remaining"] <= 0:
            resp = jsonify(
                {
                    "error": "Monthly API request quota exceeded",
                    "plan": q["plan"],
                    "limit": q["limit"],
                    "used": q["used"],
                    "upgrade_url": "/pricing",
                }
            )
            resp.status_code = 429
            resp.headers.update(quota_headers(user_id))
            return resp
        return view(*args, **kwargs)

    return wrapper
