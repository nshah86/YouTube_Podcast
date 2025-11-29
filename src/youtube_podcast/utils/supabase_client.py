"""
Supabase client initialization and utilities for VideoTranscript Pro.
"""
import os
from typing import Optional

# Try to import Supabase (optional dependency)
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

# Initialize Supabase client
supabase_url = os.getenv("REACT_APP_SUPABASE_URL") or os.getenv("SUPABASE_URL", "")
supabase_key = os.getenv("REACT_APP_SUPABASE_ANON_KEY") or os.getenv("SUPABASE_ANON_KEY", "")

supabase = None

if SUPABASE_AVAILABLE and supabase_url and supabase_key:
    try:
        supabase = create_client(supabase_url, supabase_key)
    except Exception as e:
        print(f"Warning: Failed to initialize Supabase client: {str(e)}")
        supabase = None
elif not SUPABASE_AVAILABLE:
    print("Warning: Supabase package not installed. Run: pip install supabase")
elif not (supabase_url and supabase_key):
    print("Warning: Supabase credentials not found in environment variables")


def get_supabase() -> Optional[Client]:
    """Get the Supabase client instance."""
    return supabase


def is_supabase_configured() -> bool:
    """Check if Supabase is properly configured."""
    return supabase is not None

