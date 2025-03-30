import os
import time
from datetime import datetime
from typing import Dict

from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from ..config.settings import OPENAI_API_KEY, DEFAULT_OUTPUT_DIR
from ..utils.title_generator import generate_summary_title, clean_title_for_filename

def generate_summary(state: Dict) -> Dict:
    """Generate a comprehensive summary of the YouTube video transcript"""
    if state["status"] != "transcript_fetched":
        state["error"] = "No transcript available"
        return state
    
    try:
        # Setup the LLM
        llm = ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model_name="gpt-3.5-turbo",
            temperature=0.3
        )
        
        # Define the prompt templates
        system_prompt = """You are an AI assistant tasked with creating comprehensive summaries of YouTube videos.
        
        Your summary should:
        - Be comprehensive and informative
        - Cover all key points and main ideas from the transcript
        - Be well-structured with clear organization
        - Be approximately 400-600 words
        - Use clear, concise language
        - Maintain the original meaning without adding new information
        """
        
        human_prompt = """Here is a transcript from a YouTube video:
        
        {transcript}
        
        Please provide a comprehensive summary of this video.
        """
        
        # Create the prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt)
        ])
        
        # Create the generation chain
        generation_chain = (
            {"transcript": RunnablePassthrough()}
            | prompt
            | llm
        )
        
        # Generate the summary
        transcript = state["transcript"]
        ai_message = generation_chain.invoke(transcript)
        summary = ai_message.content
        
        # Generate a title for the summary
        summary_title = generate_summary_title(summary)
        
        # Create output directory if it doesn't exist
        os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
        
        # Create a suitable filename
        if summary_title:
            # Clean title to use as filename
            clean_title = clean_title_for_filename(summary_title)
            current_date = datetime.now().strftime("%Y%m%d")
            summary_filename = f"{clean_title}_{current_date}.txt"
        else:
            # Fallback to date-based filename
            current_date = datetime.now().strftime("%Y%m%d")
            summary_filename = f"summary_{current_date}.txt"
        
        # Full path to summary file
        summary_path = os.path.join(DEFAULT_OUTPUT_DIR, summary_filename)
        
        # Create the formatted summary with title
        formatted_summary = f"{summary_title}\n\n{summary}" if summary_title else summary
        
        # Write the summary to a file
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(formatted_summary)
        
        # Update the state
        state["summary"] = summary
        state["summary_title"] = summary_title if summary_title else "Summary"
        state["summary_filename"] = summary_path
        state["status"] = "summary_generated"
        
        return state
        
    except Exception as e:
        state["error"] = f"Summary generation failed: {str(e)}"
        state["status"] = "error"
        return state
