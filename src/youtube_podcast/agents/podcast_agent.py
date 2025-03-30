from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from gtts import gTTS
from ..models.state import AgentState
from ..config.settings import OPENAI_API_KEY, DEFAULT_LLM_MODEL, DEFAULT_LANGUAGE_CODE, DEFAULT_OUTPUT_FILENAME
import os
import re
from datetime import datetime

# Set environment variables
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

def create_conversation(state: AgentState) -> AgentState:
    """Create a conversational summary between 2 people from the transcript."""
    try:
        print("Creating conversational podcast script...")
        if not state.get("transcript"):
            state["error"] = "No transcript available to create conversation."
            state["status"] = "error"
            return state
        
        # Initialize model
        model = ChatOpenAI(model=DEFAULT_LLM_MODEL)
        
        # Generate conversation
        gender_preference = state.get("gender", "neutral")
        host_names = "Alex and Jamie" if gender_preference == "neutral" else (
            "Michael and David" if gender_preference == "male" else "Sarah and Emily")
        
        prompt = SystemMessage(content=f"""
        Transform the following transcript into an engaging conversation between two hosts named {host_names}.
        Make it sound natural, with back-and-forth discussion about the key points.
        Include some light banter and personality:
        
        {state["transcript"]}
        """)
        
        response = model.invoke([prompt])
        conversation = response.content
        
        # Generate a title for the podcast
        title_prompt = SystemMessage(content=f"""
        Create a catchy, descriptive title for a podcast episode based on this conversation transcript.
        The title should be concise (5-8 words), engaging, and clearly indicate the main topic.
        Don't use quotes in the title. Just return the title text.
        
        CONVERSATION:
        {conversation[:1000]}  # Using first 1000 chars for efficiency
        """)
        
        title_response = model.invoke([title_prompt])
        podcast_title = title_response.content.strip()
        
        # Clean the title to make it suitable for a filename
        clean_title = re.sub(r'[^\w\s-]', '', podcast_title)  # Remove special chars
        clean_title = re.sub(r'\s+', '_', clean_title)        # Replace spaces with underscores
        
        state["podcast_title"] = podcast_title
        state["conversation"] = conversation
        state["status"] = "conversation_created"
        print(f"Conversation script created with title: {podcast_title}")
        
        return state
    except Exception as e:
        state["error"] = str(e)
        state["status"] = "error"
        print(f"Error creating conversation: {str(e)}")
        return state

def generate_podcast(state: AgentState) -> AgentState:
    """Generate an audio podcast from the conversation script."""
    try:
        print("Generating podcast audio file...")
        if not state.get("conversation"):
            state["error"] = "No conversation script available to convert to podcast."
            state["status"] = "error"
            return state
        
        # Generate a filename using the title if available, otherwise use date + default name
        if state.get("podcast_title"):
            clean_title = re.sub(r'[^\w\s-]', '', state["podcast_title"])
            clean_title = re.sub(r'\s+', '_', clean_title)
            filename = f"{clean_title}.mp3"
        else:
            date_str = datetime.now().strftime("%Y%m%d")
            filename = f"podcast_{date_str}.mp3"
        
        tts = gTTS(text=state["conversation"], lang=DEFAULT_LANGUAGE_CODE, slow=False)
        tts.save(filename)
        
        state["audio_path"] = filename
        state["status"] = "podcast_generated"
        print(f"Podcast generation complete: {filename}")
        
        return state
    except Exception as e:
        state["error"] = str(e)
        state["status"] = "error"
        print(f"Error generating podcast: {str(e)}")
        return state
