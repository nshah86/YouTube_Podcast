from langgraph.graph import StateGraph, START, END
from .models.state import AgentState
from .agents.transcript_agent import get_url_input, fetch_transcript, get_output_preferences
from .agents.summary_agent import generate_summary
from .agents.podcast_agent import create_conversation, generate_podcast
from .config.settings import DEBUG_LANGGRAPH, DEBUG_LANGGRAPH_PORT

def determine_output_path(state: AgentState) -> str:
    """Determine which path to take based on user's choice."""
    return state["output_type"]

def create_workflow(debug: bool = False) -> StateGraph:
    """Create a workflow graph with conditional branches."""
    workflow = StateGraph(AgentState)
    
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
    compiled_workflow = workflow.compile()
    
    # Set up debugging visualization if requested
    if debug:
        from langgraph.checkpoint import MemorySaver
        from langgraph.websocket import WebSocketServer
        
        memory_saver = MemorySaver()
        websocket_server = WebSocketServer(memory_saver, port=DEBUG_LANGGRAPH_PORT)
        
        # Start the websocket server for visualization
        websocket_server.start()
        print(f"Debug visualization server started on port {DEBUG_LANGGRAPH_PORT}. Open http://localhost:{DEBUG_LANGGRAPH_PORT} to view the workflow graph.")
        
        # Register the checkpoint with the compiled workflow
        compiled_workflow.with_checkpointer(memory_saver)
    
    return compiled_workflow

def run_workflow(debug: bool = False):
    """Run the YouTube processing workflow with conditional paths."""
    # Initialize the state
    initial_state = AgentState(
        url="",
        transcript="",
        summary="",
        conversation="",
        audio_path="",
        output_type="",
        gender=None,
        debug=debug,
        status="initialized",
        error=None
    )
    
    # Create and run the workflow
    workflow = create_workflow(debug=debug)
    final_state = workflow.invoke(initial_state)
    
    # Display final output
    print("\nWorkflow completed!")
    if final_state['status'] == 'error':
        print(f"Error occurred during processing: {final_state['error']}")
    elif final_state['output_type'] == 'summary':
        print("\nSummary of the video:")
        print(final_state['summary'])
    else:  # podcast
        print(f"\nPodcast audio file generated: {final_state['audio_path']}")
        print("\nConversation script used for the podcast:")
        print(final_state['conversation'])
        
    return final_state
