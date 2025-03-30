from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from ..models.state import AgentState
from ..config.settings import OPENAI_API_KEY, DEFAULT_LLM_MODEL
import os
import re
from datetime import datetime

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
        
        # Generate a title for the summary
        title_prompt = SystemMessage(content=f"""
        Create a clear, descriptive title for this content summary.
        The title should be concise (4-7 words) and clearly indicate the main topic.
        Don't use quotes in the title. Just return the title text.
        
        SUMMARY:
        {summary[:1000]}  # Using first 1000 chars for efficiency
        """)
        
        title_response = model.invoke([title_prompt])
        summary_title = title_response.content.strip()
        
        # Clean the title to make it suitable for a filename
        clean_title = re.sub(r'[^\w\s-]', '', summary_title)  # Remove special chars
        clean_title = re.sub(r'\s+', '_', clean_title)        # Replace spaces with underscores
        
        # Create a filename for the summary
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"{clean_title}_{date_str}.txt"
        
        # Save the summary to a file
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# {summary_title}\n\n")
                f.write(summary)
        except Exception as e:
            print(f"Warning: Could not save summary to file: {str(e)}")
        
        state["summary"] = summary
        state["summary_title"] = summary_title
        state["summary_filename"] = filename
        state["status"] = "summary_generated"
        print(f"Summary generation complete with title: {summary_title}")
        
        return state
    except Exception as e:
        state["error"] = str(e)
        state["status"] = "error"
        print(f"Error generating summary: {str(e)}")
        return state
