"""
Usage tracking utilities for VideoTranscript Pro.
Tracks user activities in Supabase usage_history table.
"""
import os
import sys
from typing import Optional, Dict
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from src.youtube_podcast.utils.supabase_client import get_supabase, is_supabase_configured
from src.youtube_podcast.utils.youtube_utils import extract_video_id


def track_usage(
    user_id: str,
    video_url: str,
    operation_type: str,
    transcript_length: int = 0,
    tokens_used: int = 1
) -> bool:
    """
    Track user activity in Supabase usage_history table.
    
    Args:
        user_id: User UUID
        video_url: YouTube video URL
        operation_type: 'extract', 'summary', or 'podcast'
        transcript_length: Length of transcript in characters
        tokens_used: Number of tokens consumed
        
    Returns:
        True if tracking successful, False otherwise
    """
    try:
        if not is_supabase_configured():
            return False
        
        supabase = get_supabase()
        video_id = extract_video_id(video_url) if video_url else None
        
        # Insert usage record
        response = supabase.table('usage_history').insert({
            'user_id': user_id,
            'video_id': video_id,
            'video_url': video_url,
            'transcript_length': transcript_length,
            'operation_type': operation_type,
            'tokens_used': tokens_used
        }).execute()
        
        # Update user token usage
        update_user_token_usage(user_id, tokens_used)
        
        return True
    
    except Exception as e:
        print(f"Error tracking usage: {str(e)}")
        return False


def update_user_token_usage(user_id: str, tokens_used: int) -> bool:
    """
    Update user's token usage count in user_profiles table.
    
    Args:
        user_id: User UUID
        tokens_used: Number of tokens to add to usage count
        
    Returns:
        True if update successful, False otherwise
    """
    try:
        if not is_supabase_configured():
            return False
        
        supabase = get_supabase()
        
        # Get current usage
        profile_response = supabase.table('user_profiles').select('tokens_used').eq('id', user_id).execute()
        
        if profile_response.data:
            current_used = profile_response.data[0].get('tokens_used', 0)
            new_used = current_used + tokens_used
            
            # Update usage
            supabase.table('user_profiles').update({
                'tokens_used': new_used,
                'updated_at': datetime.now().isoformat()
            }).eq('id', user_id).execute()
            
            return True
        
        return False
    
    except Exception as e:
        print(f"Error updating token usage: {str(e)}")
        return False


def get_user_usage_history(user_id: str, limit: int = 50) -> list:
    """
    Get user's usage history from Supabase.
    
    Args:
        user_id: User UUID
        limit: Maximum number of records to return
        
    Returns:
        List of usage history records
    """
    try:
        if not is_supabase_configured():
            return []
        
        supabase = get_supabase()
        
        response = supabase.table('usage_history')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .limit(limit)\
            .execute()
        
        return response.data or []
    
    except Exception as e:
        print(f"Error fetching usage history: {str(e)}")
        return []


def get_user_usage_stats(user_id: str) -> Dict:
    """
    Get user's usage statistics.
    
    Args:
        user_id: User UUID
        
    Returns:
        Dictionary with usage statistics
    """
    try:
        if not is_supabase_configured():
            return {}
        
        supabase = get_supabase()
        
        # Get profile
        profile_response = supabase.table('user_profiles').select('*').eq('id', user_id).execute()
        
        if not profile_response.data:
            return {}
        
        profile = profile_response.data[0]
        
        # Get usage history count
        history_response = supabase.table('usage_history')\
            .select('id', count='exact')\
            .eq('user_id', user_id)\
            .execute()
        
        total_operations = history_response.count if hasattr(history_response, 'count') else 0
        
        return {
            'tokens_used': profile.get('tokens_used', 0),
            'tokens_limit': profile.get('tokens_limit', 25),
            'plan': profile.get('plan', 'free'),
            'total_operations': total_operations,
            'tokens_remaining': max(0, profile.get('tokens_limit', 25) - profile.get('tokens_used', 0))
        }
    
    except Exception as e:
        print(f"Error fetching usage stats: {str(e)}")
        return {}

