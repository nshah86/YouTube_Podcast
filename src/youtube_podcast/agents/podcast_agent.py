from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from gtts import gTTS
from ..models.state import AgentState
from ..config.settings import OPENAI_API_KEY, DEFAULT_LLM_MODEL, DEFAULT_LANGUAGE_CODE, DEFAULT_OUTPUT_FILENAME
import os

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
        
        state["conversation"] = conversation
        state["status"] = "conversation_created"
        print("Conversation script created.")
        
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
            
        output_filename = DEFAULT_OUTPUT_FILENAME
        
        tts = gTTS(text=state["conversation"], lang=DEFAULT_LANGUAGE_CODE, slow=False)
        tts.save(output_filename)
        
        state["audio_path"] = output_filename
        state["status"] = "podcast_generated"
        print(f"Podcast generation complete: {output_filename}")
        
        return state
    except Exception as e:
        state["error"] = str(e)
        state["status"] = "error"
        print(f"Error generating podcast: {str(e)}")
        return state
