from typing import TypedDict, Optional

class AgentState(TypedDict):
    """State model for the YouTube podcast generator workflow"""
    url: str
    transcript: str
    summary: str
    conversation: str
    audio_path: str
    output_type: str
    gender: Optional[str]  # 'male' or 'female' for podcast voice
    debug: bool  # To enable debug visualization
    
    # For tracking progress through the workflow
    status: str
    error: Optional[str]
