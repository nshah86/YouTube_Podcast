"""
Rate limiting utilities for VideoTranscript Pro.
Implements per-user rate limiting using Supabase.
"""
import time
from typing import Optional, Dict
from datetime import datetime, timedelta
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from src.youtube_podcast.utils.supabase_client import get_supabase, is_supabase_configured


# In-memory rate limit cache (for performance)
_rate_limit_cache: Dict[str, Dict] = {}


def check_rate_limit(user_id: Optional[str] = None, endpoint: str = "default") -> tuple[bool, Optional[str]]:
    """
    Check if user has exceeded rate limit.
    
    Args:
        user_id: User UUID (optional, for authenticated users)
        endpoint: Endpoint name for different rate limits
        
    Returns:
        (is_allowed, error_message)
    """
    # Default rate limits (requests per time window)
    rate_limits = {
        "default": {"requests": 5, "window": 10},  # 5 requests per 10 seconds
        "extract": {"requests": 10, "window": 60},  # 10 requests per minute
        "api": {"requests": 5, "window": 10},  # 5 requests per 10 seconds
    }
    
    limit_config = rate_limits.get(endpoint, rate_limits["default"])
    max_requests = limit_config["requests"]
    window_seconds = limit_config["window"]
    
    # Use user_id or IP address as key
    cache_key = f"{user_id or 'anonymous'}_{endpoint}"
    current_time = time.time()
    
    # Check in-memory cache first
    if cache_key in _rate_limit_cache:
        cache_entry = _rate_limit_cache[cache_key]
        
        # Remove old requests outside the window
        cache_entry["requests"] = [
            req_time for req_time in cache_entry["requests"]
            if current_time - req_time < window_seconds
        ]
        
        # Check if limit exceeded
        if len(cache_entry["requests"]) >= max_requests:
            oldest_request = min(cache_entry["requests"])
            retry_after = int(window_seconds - (current_time - oldest_request)) + 1
            return False, f"Rate limit exceeded. Try again in {retry_after} seconds."
        
        # Add current request
        cache_entry["requests"].append(current_time)
    else:
        # Create new cache entry
        _rate_limit_cache[cache_key] = {
            "requests": [current_time],
            "last_cleanup": current_time
        }
    
    # Cleanup old cache entries periodically
    if current_time - _rate_limit_cache.get(cache_key, {}).get("last_cleanup", 0) > 300:
        cleanup_rate_limit_cache()
        if cache_key in _rate_limit_cache:
            _rate_limit_cache[cache_key]["last_cleanup"] = current_time
    
    return True, None


def cleanup_rate_limit_cache():
    """Remove old entries from rate limit cache."""
    current_time = time.time()
    keys_to_remove = []
    
    for key, entry in _rate_limit_cache.items():
        # Remove entries older than 5 minutes
        if current_time - entry.get("last_cleanup", current_time) > 300:
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del _rate_limit_cache[key]


def requires_rate_limit(f):
    """Decorator to add rate limiting to Flask routes."""
    from functools import wraps
    from flask import request, jsonify, session
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        endpoint = request.endpoint or "default"
        
        is_allowed, error_msg = check_rate_limit(user_id, endpoint)
        
        if not is_allowed:
            return jsonify({
                'error': error_msg,
                'retry_after': 10
            }), 429
        
        return f(*args, **kwargs)
    
    return decorated_function

