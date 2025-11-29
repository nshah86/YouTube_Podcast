"""
API Authentication utilities for VideoTranscript Pro.
"""
from functools import wraps
from flask import request, jsonify
import os
import sys
import base64
from typing import Optional, Dict


# In production, this would be stored in a database
# For now, we'll use environment variables or a simple file
API_TOKENS = {
    # Format: "token": {"plan": "free|plus|pro|enterprise", "tokens_used": 0, "tokens_limit": 25}
    # Example tokens (in production, generate these securely)
    os.getenv("API_TOKEN_FREE", "free_token_123"): {
        "plan": "free",
        "tokens_used": 0,
        "tokens_limit": 25,
        "monthly_reset": True
    },
    os.getenv("API_TOKEN_PLUS", "plus_token_456"): {
        "plan": "plus",
        "tokens_used": 0,
        "tokens_limit": 1000,
        "monthly_reset": True
    },
    os.getenv("API_TOKEN_PRO", "pro_token_789"): {
        "plan": "pro",
        "tokens_used": 0,
        "tokens_limit": 3000,
        "monthly_reset": True
    }
}


def get_api_token_from_request() -> Optional[str]:
    """Extract API token from Authorization header."""
    auth_header = request.headers.get('Authorization', '')
    
    if not auth_header:
        return None
    
    # Support both "Basic <token>" and "Bearer <token>" formats
    if auth_header.startswith('Basic '):
        token = auth_header.replace('Basic ', '').strip()
        # Decode if it's base64 encoded
        try:
            token = base64.b64decode(token).decode('utf-8')
        except:
            pass
        return token
    elif auth_header.startswith('Bearer '):
        return auth_header.replace('Bearer ', '').strip()
    
    return auth_header.strip()


def get_user_plan(token: str) -> Optional[str]:
    """Get user plan from API token. Syncs with Supabase if available."""
    if token in API_TOKENS:
        return API_TOKENS[token].get("plan")
    
    # Try to get from Supabase if token not in cache
    try:
        import os
        sys_path = os.path.join(os.path.dirname(__file__), "..", "..", "..")
        if sys_path not in sys.path:
            sys.path.insert(0, sys_path)
        
        from src.youtube_podcast.utils.supabase_client import get_supabase, is_supabase_configured
        
        if is_supabase_configured():
            supabase = get_supabase()
            response = supabase.table('api_tokens').select('user_id').eq('token', token).execute()
            if response.data and len(response.data) > 0:
                user_id = response.data[0]['user_id']
                profile_response = supabase.table('user_profiles').select('plan').eq('id', user_id).execute()
                if profile_response.data:
                    plan = profile_response.data[0].get('plan', 'free')
                    # Cache it
                    API_TOKENS[token] = {
                        "plan": plan,
                        "tokens_used": 0,
                        "tokens_limit": 25,
                        "monthly_reset": True
                    }
                    return plan
    except Exception:
        pass  # Fallback to cache only
    
    return None


def check_rate_limit(token: str) -> bool:
    """Check if user has exceeded rate limit (5 requests per 10 seconds)."""
    # In production, use Redis or similar for rate limiting
    # For now, we'll do a simple check
    return True  # Placeholder - implement proper rate limiting


def check_token_limit(token: str, count: int = 1):
    """
    Check if user has enough tokens remaining.
    Returns (has_limit, error_message)
    """
    if token not in API_TOKENS:
        return False, "Invalid API token"
    
    user_data = API_TOKENS[token]
    tokens_used = user_data.get("tokens_used", 0)
    tokens_limit = user_data.get("tokens_limit", 0)
    
    if tokens_used + count > tokens_limit:
        return False, f"Token limit exceeded. Used {tokens_used}/{tokens_limit}"
    
    return True, None


def increment_token_usage(token: str, count: int = 1):
    """Increment token usage counter."""
    if token in API_TOKENS:
        API_TOKENS[token]["tokens_used"] += count


def requires_auth(f):
    """Decorator to require API authentication with database tracking."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        import time
        from flask import request as flask_request
        from src.youtube_podcast.utils.api_tracker import track_api_usage, get_api_token_id_from_token
        
        start_time = time.time()
        token = get_api_token_from_request()
        
        if not token:
            return jsonify({
                'error': 'Authorization required. Include Authorization header with your API token.'
            }), 401
        
        # Check token in database first, then cache
        user_id = None
        api_token_id = None
        
        try:
            import os
            sys_path = os.path.join(os.path.dirname(__file__), "..", "..", "..")
            if sys_path not in sys.path:
                sys.path.insert(0, sys_path)
            
            from src.youtube_podcast.utils.supabase_client import get_supabase, is_supabase_configured
            
            if is_supabase_configured():
                supabase = get_supabase()
                token_response = supabase.table('api_tokens').select('id, user_id').eq('token', token).execute()
                
                if token_response.data and len(token_response.data) > 0:
                    api_token_id = token_response.data[0]['id']
                    user_id = token_response.data[0]['user_id']
                    
                    # Get user plan from profile
                    profile_response = supabase.table('user_profiles').select('plan, tokens_limit, tokens_used').eq('id', user_id).execute()
                    if profile_response.data:
                        plan = profile_response.data[0].get('plan', 'free')
                        tokens_limit = profile_response.data[0].get('tokens_limit', 25)
                        tokens_used = profile_response.data[0].get('tokens_used', 0)
                        
                        # Check token limit
                        if tokens_used >= tokens_limit:
                            response_time = int((time.time() - start_time) * 1000)
                            track_api_usage(
                                api_token_id=api_token_id,
                                user_id=user_id,
                                endpoint=flask_request.path,
                                method=flask_request.method,
                                status_code=403,
                                tokens_used=0,
                                response_time_ms=response_time,
                                ip_address=flask_request.remote_addr,
                                user_agent=flask_request.headers.get('User-Agent')
                            )
                            return jsonify({
                                'error': f'Token limit exceeded. Used {tokens_used}/{tokens_limit}'
                            }), 403
                        
                        # Cache token info
                        if token not in API_TOKENS:
                            API_TOKENS[token] = {
                                "plan": plan,
                                "tokens_used": tokens_used,
                                "tokens_limit": tokens_limit,
                                "monthly_reset": True,
                                "user_id": user_id
                            }
                        else:
                            # Update cache with latest from DB
                            API_TOKENS[token]["plan"] = plan
                            API_TOKENS[token]["tokens_used"] = tokens_used
                            API_TOKENS[token]["tokens_limit"] = tokens_limit
                            API_TOKENS[token]["user_id"] = user_id
        except Exception as e:
            # Fallback to cache if DB check fails
            pass
        
        # Fallback to cache if not in database
        if token not in API_TOKENS:
            return jsonify({
                'error': 'Invalid API token. Please check your token and try again.'
            }), 401
        
        # Check rate limit
        if not check_rate_limit(token):
            response_time = int((time.time() - start_time) * 1000)
            if api_token_id and user_id:
                track_api_usage(
                    api_token_id=api_token_id,
                    user_id=user_id,
                    endpoint=flask_request.path,
                    method=flask_request.method,
                    status_code=429,
                    tokens_used=0,
                    response_time_ms=response_time,
                    ip_address=flask_request.remote_addr,
                    user_agent=flask_request.headers.get('User-Agent')
                )
            return jsonify({
                'error': 'Rate limit exceeded. Please wait before making another request.'
            }), 429
        
        # Attach user info to request
        flask_request.api_token = token
        flask_request.user_plan = get_user_plan(token)
        flask_request.user_data = API_TOKENS[token]
        flask_request.api_token_id = api_token_id
        flask_request.api_user_id = user_id or API_TOKENS[token].get("user_id")
        
        # Execute the function
        try:
            response = f(*args, **kwargs)
            response_time = int((time.time() - start_time) * 1000)
            
            # Track successful API call
            if api_token_id and user_id:
                status_code = response[1] if isinstance(response, tuple) else 200
                tokens_used = 1  # Default, can be overridden
                
                track_api_usage(
                    api_token_id=api_token_id,
                    user_id=user_id,
                    endpoint=flask_request.path,
                    method=flask_request.method,
                    status_code=status_code,
                    tokens_used=tokens_used,
                    response_time_ms=response_time,
                    ip_address=flask_request.remote_addr,
                    user_agent=flask_request.headers.get('User-Agent')
                )
            
            return response
        except Exception as e:
            # Track failed API call
            response_time = int((time.time() - start_time) * 1000)
            if api_token_id and user_id:
                track_api_usage(
                    api_token_id=api_token_id,
                    user_id=user_id,
                    endpoint=flask_request.path,
                    method=flask_request.method,
                    status_code=500,
                    tokens_used=0,
                    response_time_ms=response_time,
                    ip_address=flask_request.remote_addr,
                    user_agent=flask_request.headers.get('User-Agent')
                )
            raise
    
    return decorated_function


def requires_plan(min_plan: str):
    """
    Decorator to require a minimum plan level.
    Plan hierarchy: free < plus < pro < enterprise
    """
    plan_levels = {
        'free': 0,
        'plus': 1,
        'pro': 2,
        'enterprise': 3
    }
    
    def decorator(f):
        @wraps(f)
        @requires_auth
        def decorated_function(*args, **kwargs):
            user_plan = request.user_plan
            user_level = plan_levels.get(user_plan, -1)
            required_level = plan_levels.get(min_plan, 0)
            
            if user_level < required_level:
                return jsonify({
                    'error': f'This endpoint requires {min_plan} plan or higher. Your current plan: {user_plan}'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

