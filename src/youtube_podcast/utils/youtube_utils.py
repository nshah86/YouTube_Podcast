from youtube_transcript_api import YouTubeTranscriptApi
from typing import Optional
from ..models.state import AgentState

def extract_video_id(url: str) -> str:
    """Extract the YouTube video ID from a URL."""
    if "watch?v=" in url:
        return url.split("watch?v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    else:
        raise ValueError("Invalid YouTube URL format")

def fetch_transcript(video_url: str) -> Optional[str]:
    """Fetch transcript from a YouTube video URL."""
    try:
        video_id = extract_video_id(video_url)
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        text = " ".join([entry['text'] for entry in transcript])
        return text
    except Exception as e:
        print(f"Error fetching transcript: {str(e)}")
        return None

def update_transcript_in_state(state: AgentState) -> AgentState:
    """Update the state with the fetched transcript."""
    try:
        print(f"Fetching transcript from URL: {state['url']}...")
        transcript = fetch_transcript(state['url'])
        
        if transcript:
            state["transcript"] = transcript
            state["status"] = "transcript_fetched"
            print("Transcript fetched successfully.")
        else:
            state["error"] = "Failed to fetch transcript"
            state["status"] = "error"
            
        return state
    except Exception as e:
        state["error"] = str(e)
        state["status"] = "error"
        print(f"Error in transcript agent: {str(e)}")
        return state
