from langgraph.graph import StateGraph, START, END
from .agents.transcript_agent import get_url_input, fetch_transcript, get_output_preferences
from .agents.summary_agent import generate_summary
from .agents.podcast_agent import create_conversation, generate_podcast
from typing import Dict
import os
from datetime import datetime

try:
    from .config.settings import DEFAULT_OUTPUT_DIR
except ImportError:
    # Fallback if DEFAULT_OUTPUT_DIR is not defined
    DEFAULT_OUTPUT_DIR = os.path.join(os.getcwd(), "output")
    os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)

def determine_output_path(state: Dict) -> str:
    """Determine which path to take based on user's choice."""
    return state["output_type"]

def create_workflow() -> StateGraph:
    """Create a workflow graph with conditional branches."""
    workflow = StateGraph(Dict)
    
    # Add nodes
    workflow.add_node("get_url_node", get_url_input)
    workflow.add_node("fetch_transcript_node", fetch_transcript)
    workflow.add_node("get_preferences_node", get_output_preferences)
    workflow.add_node("summary_node", generate_summary)
    workflow.add_node("conversation_node", create_conversation)
    workflow.add_node("podcast_node", generate_podcast)
    
    # Add edges
    workflow.add_edge(START, "get_url_node")
    workflow.add_edge("get_url_node", "fetch_transcript_node")
    workflow.add_edge("fetch_transcript_node", "get_preferences_node")
    
    # Add conditional edges based on user choice
    workflow.add_conditional_edges(
        "get_preferences_node",
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

def initialize_state() -> Dict:
    """
    Initialize the state dictionary with default values.
    
    This function creates a centralized way to initialize the state with
    default values and ensure consistency across the application.
    
    Returns:
        Dict: A dictionary with initial state values
    """
    # Create output directory if it doesn't exist
    os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
    
    # Initialize with default values
    return {
        "url": "",
        "transcript": "",
        "summary": "",
        "summary_title": "",
        "summary_filename": "",
        "conversation": "",
        "podcast_title": "",
        "podcast_filename": "",
        "audio_path": "",
        "gender": "mixed",
        "output_type": "summary",
        "status": "initialized",
        "error": None,
        "start_time": datetime.now().isoformat(),
    }

def run_workflow():
    """Run the YouTube processing workflow with conditional paths."""
    # Initialize the state
    initial_state = initialize_state()
    
    # Create and run the workflow
    workflow = create_workflow()
    final_state = workflow.invoke(initial_state)
    
    return final_state
