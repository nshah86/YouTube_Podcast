from typing import TypedDict, Optional

class AgentState(TypedDict):
    """State model for the YouTube podcast generator workflow"""
    url: str
    transcript: str
    summary: str
    summary_title: Optional[str]
    summary_filename: Optional[str]
    conversation: str
    podcast_title: Optional[str]
    audio_path: str
    output_type: str
    gender: Optional[str]  # 'male' or 'female' for podcast voice
    
    # For tracking progress through the workflow
    status: str
    error: Optional[str]
