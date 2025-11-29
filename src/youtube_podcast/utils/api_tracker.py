"""
API usage tracking utilities for VideoTranscript Pro.
Tracks API calls in the database for security and analytics.
"""
import os
import sys
import logging
from typing import Optional, Dict
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from src.youtube_podcast.utils.supabase_client import get_supabase, is_supabase_configured

logger = logging.getLogger(__name__)


def track_api_usage(
    api_token_id: str,
    user_id: str,
    endpoint: str,
    method: str,
    status_code: int,
    tokens_used: int = 1,
    response_time_ms: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> bool:
    """
    Track API usage in the database.
    
    Args:
        api_token_id: API token UUID
        user_id: User UUID
        endpoint: API endpoint called
        method: HTTP method (GET, POST, etc.)
        status_code: HTTP status code
        tokens_used: Number of tokens consumed
        response_time_ms: Response time in milliseconds
        ip_address: Client IP address
        user_agent: Client user agent
        
    Returns:
        True if tracking successful, False otherwise
    """
    try:
        if not is_supabase_configured():
            return False
        
        supabase = get_supabase()
        
        # Insert API usage record
        supabase.table('api_usage').insert({
            'api_token_id': api_token_id,
            'user_id': user_id,
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'tokens_used': tokens_used,
            'response_time_ms': response_time_ms,
            'ip_address': ip_address,
            'user_agent': user_agent
        }).execute()
        
        return True
    
    except Exception as e:
        logger.error(f"Error tracking API usage: {str(e)}")
        return False


def get_api_token_id_from_token(token: str) -> Optional[str]:
    """
    Get API token ID from token string.
    
    Args:
        token: API token string
        
    Returns:
        API token UUID or None if not found
    """
    try:
        if not is_supabase_configured():
            return None
        
        supabase = get_supabase()
        
        response = supabase.table('api_tokens').select('id').eq('token', token).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]['id']
        
        return None
    
    except Exception as e:
        logger.error(f"Error getting API token ID: {str(e)}")
        return None


def get_user_api_usage_stats(user_id: str, days: int = 30) -> Dict:
    """
    Get user's API usage statistics.
    
    Args:
        user_id: User UUID
        days: Number of days to look back
        
    Returns:
        Dictionary with usage statistics
    """
    try:
        if not is_supabase_configured():
            return {}
        
        supabase = get_supabase()
        
        # Get usage records
        from datetime import timedelta
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        response = supabase.table('api_usage')\
            .select('*')\
            .eq('user_id', user_id)\
            .gte('created_at', cutoff_date)\
            .execute()
        
        records = response.data or []
        
        # Calculate statistics
        total_calls = len(records)
        successful_calls = sum(1 for r in records if r.get('status_code', 0) < 400)
        failed_calls = total_calls - successful_calls
        total_tokens = sum(r.get('tokens_used', 0) for r in records)
        avg_response_time = sum(r.get('response_time_ms', 0) for r in records) / total_calls if total_calls > 0 else 0
        
        # Group by endpoint
        endpoint_stats = {}
        for record in records:
            endpoint = record.get('endpoint', 'unknown')
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = {'calls': 0, 'tokens': 0}
            endpoint_stats[endpoint]['calls'] += 1
            endpoint_stats[endpoint]['tokens'] += record.get('tokens_used', 0)
        
        return {
            'total_calls': total_calls,
            'successful_calls': successful_calls,
            'failed_calls': failed_calls,
            'total_tokens_used': total_tokens,
            'avg_response_time_ms': avg_response_time,
            'endpoint_stats': endpoint_stats
        }
    
    except Exception as e:
        logger.error(f"Error getting API usage stats: {str(e)}")
        return {}

