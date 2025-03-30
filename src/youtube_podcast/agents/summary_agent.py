from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from ..models.state import AgentState
from ..config.settings import OPENAI_API_KEY, DEFAULT_LLM_MODEL
import os

# Set environment variables
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

def generate_summary(state: AgentState) -> AgentState:
    """Generate a text summary of the transcript."""
    try:
        print("Generating summary...")
        if not state.get("transcript"):
            state["error"] = "No transcript available to summarize."
            state["status"] = "error"
            return state
        
        # Initialize model
        model = ChatOpenAI(model=DEFAULT_LLM_MODEL)
        
        # Generate summary
        prompt = SystemMessage(content=f'Summarize the following video transcript concisely: {state["transcript"]}')
        response = model.invoke([prompt])
        summary = response.content
        
        state["summary"] = summary
        state["status"] = "summary_generated"
        print("Summary generation complete.")
        
        return state
    except Exception as e:
        state["error"] = str(e)
        state["status"] = "error"
        print(f"Error generating summary: {str(e)}")
        return state
