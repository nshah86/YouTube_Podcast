import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from youtube_transcript_api import YouTubeTranscriptApi
from gtts import gTTS
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Dict, Any
from typing_extensions import TypedDict

# Load environment variables
load_dotenv()
os.environ['OPENAI_API_KEY'] = os.getenv("OPENAI_API_KEY")

# Initialize the model
model = ChatOpenAI(model="gpt-4o")

# Define the state structure
class AgentState(TypedDict):
    url: str
    transcript: str
    summary: str
    conversation: str
    audio_path: str
    output_type: str

def extract_video_id(url: str) -> str:
    """Extract the YouTube video ID from a URL."""
    if "watch?v=" in url:
        return url.split("watch?v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    else:
        raise ValueError("Invalid YouTube URL format")

def get_url_input(state: AgentState) -> AgentState:
    """Get the YouTube URL from the user."""
    url = input("Enter the YouTube video URL: ")
    state["url"] = url
    return state

def fetch_transcript(state: AgentState) -> AgentState:
    """Fetch transcript from the YouTube video."""
    try:
        print(f"Fetching transcript from URL: {state['url']}...")
        video_id = extract_video_id(state["url"])
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        text = " ".join([entry['text'] for entry in transcript])
        
        state["transcript"] = text
        print("Transcript fetched successfully.")
        return state
    except Exception as e:
        print(f"Error fetching transcript: {str(e)}")
        state["transcript"] = ""
        return state

def get_output_choice(state: AgentState) -> AgentState:
    """Ask the user for their output preference (summary or podcast)."""
    while True:
        output_choice = input("Do you want a summary (text output) or podcast (audio file)? Enter 'summary' or 'podcast': ").lower().strip()
        if output_choice in ["summary", "podcast"]:
            break
        print("Invalid choice. Please enter 'summary' or 'podcast'.")
    
    state["output_type"] = output_choice
    return state

def generate_summary(state: AgentState) -> AgentState:
    """Generate a text summary of the transcript."""
    try:
        print("Generating summary...")
        if not state.get("transcript"):
            print("No transcript available to summarize.")
            return state
            
        prompt = SystemMessage(content=f'Summarize the following video transcript concisely: {state["transcript"]}')
        response = model.invoke([prompt])
        summary = response.content
        
        state["summary"] = summary
        print("Summary generation complete.")
        
        return state
    except Exception as e:
        print(f"Error generating summary: {str(e)}")
        return state

def create_conversation(state: AgentState) -> AgentState:
    """Create a conversational summary between 2 people from the transcript."""
    try:
        print("Creating conversational podcast script...")
        if not state.get("transcript"):
            print("No transcript available to create conversation.")
            return state
        
        prompt = SystemMessage(content=f"""
        Transform the following transcript into an engaging conversation between two hosts named Alex and Jamie.
        Make it sound natural, with back-and-forth discussion about the key points.
        Include some light banter and personality:
        
        {state["transcript"]}
        """)
        
        response = model.invoke([prompt])
        conversation = response.content
        
        state["conversation"] = conversation
        print("Conversation script created.")
        
        return state
    except Exception as e:
        print(f"Error creating conversation: {str(e)}")
        return state

def generate_podcast(state: AgentState) -> AgentState:
    """Generate an audio podcast from the conversation script."""
    try:
        print("Generating podcast audio file...")
        if not state.get("conversation"):
            print("No conversation script available to convert to podcast.")
            return state
            
        language_code = 'en'
        output_filename = "YT_podcast.mp3"
        
        tts = gTTS(text=state["conversation"], lang=language_code, slow=False)
        tts.save(output_filename)
        
        state["audio_path"] = output_filename
        print(f"Podcast generation complete: {output_filename}")
        
        return state
    except Exception as e:
        print(f"Error generating podcast: {str(e)}")
        return state

def determine_output_path(state: AgentState) -> str:
    """Determine which path to take based on user's choice."""
    return state["output_type"]

def create_workflow():
    """Create a workflow graph with conditional branches."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("get_url_node", get_url_input)
    workflow.add_node("fetch_transcript_node", fetch_transcript)
    workflow.add_node("get_choice_node", get_output_choice)
    workflow.add_node("summary_node", generate_summary)
    workflow.add_node("conversation_node", create_conversation)
    workflow.add_node("podcast_node", generate_podcast)
    
    # Add edges
    workflow.add_edge(START, "get_url_node")
    workflow.add_edge("get_url_node", "fetch_transcript_node")
    workflow.add_edge("fetch_transcript_node", "get_choice_node")
    
    # Add conditional edges based on user choice
    workflow.add_conditional_edges(
        "get_choice_node",
        determine_output_path,
        {
            "summary": "summary_node",
            "podcast": "conversation_node"
        }
    )
    
    # Add final edges
    workflow.add_edge("summary_node", END)
    workflow.add_edge("conversation_node", "podcast_node")
    workflow.add_edge("podcast_node", END)
    
    # Compile the workflow
    return workflow.compile()

def create_agent_workflow():
    """Alias for create_workflow for backward compatibility."""
    return create_workflow()

def main():
    """Run the YouTube processing workflow with conditional paths."""
    # Initialize the state
    initial_state = AgentState(
        url="",
        transcript="",
        summary="",
        conversation="",
        audio_path="",
        output_type=""
    )
    
    # Create and run the workflow
    workflow = create_workflow()
    final_state = workflow.invoke(initial_state)
    
    # Display final output
    print("\nWorkflow completed!")
    if final_state['output_type'] == 'summary':
        print("\nSummary of the video:")
        print(final_state['summary'])
    else:  # podcast
        print(f"\nPodcast audio file generated: {final_state['audio_path']}")
        print("\nConversation script used for the podcast:")
        print(final_state['conversation'])

if __name__ == "__main__":
    main()
