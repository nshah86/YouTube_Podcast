from ..models.state import AgentState
from ..utils.youtube_utils import update_transcript_in_state

def get_url_input(state: AgentState) -> AgentState:
    """Get the YouTube URL from the user."""
    url = input("Enter the YouTube video URL: ")
    state["url"] = url
    state["status"] = "url_received"
    return state

def fetch_transcript(state: AgentState) -> AgentState:
    """Fetch transcript from the YouTube video."""
    return update_transcript_in_state(state)

def get_output_preferences(state: AgentState) -> AgentState:
    """Ask the user for their output preference (summary or podcast) and gender for podcast."""
    while True:
        output_choice = input("Do you want a summary (text output) or podcast (audio file)? Enter 'summary' or 'podcast': ").lower().strip()
        if output_choice in ["summary", "podcast"]:
            break
        print("Invalid choice. Please enter 'summary' or 'podcast'.")
    
    state["output_type"] = output_choice
    
    if output_choice == "podcast":
        while True:
            gender_choice = input("Do you prefer a male or female voice for the podcast? Enter 'male' or 'female': ").lower().strip()
            if gender_choice in ["male", "female"]:
                break
            print("Invalid choice. Please enter 'male' or 'female'.")
        
        state["gender"] = gender_choice
    
    state["status"] = "preferences_set"
    return state
