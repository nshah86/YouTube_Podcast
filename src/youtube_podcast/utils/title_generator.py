import re
from typing import Optional
from langchain_community.chat_models import ChatOpenAI
from ..config.settings import OPENAI_API_KEY

def generate_podcast_title(conversation_text: str) -> Optional[str]:
    """
    Generate a catchy and descriptive title for a podcast based on the conversation.
    
    Args:
        conversation_text: The podcast conversation text
        
    Returns:
        A title string or None if generation fails
    """
    try:
        if not conversation_text or len(conversation_text) < 50:
            return None
            
        # Initialize ChatOpenAI
        llm = ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model_name="gpt-3.5-turbo",
            temperature=0.7
        )
        
        # Create a prompt for title generation
        # Use only the first ~1000 characters of the conversation to save tokens
        sample_text = conversation_text[:1000] if len(conversation_text) > 1000 else conversation_text
        
        prompt = f"""Create a catchy, descriptive title for a podcast episode based on this conversation:

        {sample_text}
        
        The title should be:
        - Concise (5-8 words)
        - Engaging and descriptive
        - Clearly indicate the main topic
        - No quotes or special characters
        
        Return only the title text, nothing else."""
        
        # Generate the title
        response = llm.invoke(prompt)
        
        # Clean the title (remove quotes, extra spaces, etc.)
        title = response.content.strip()
        title = re.sub(r'^["\'"]|["\'"]$', '', title)  # Remove surrounding quotes
        title = re.sub(r'\s+', ' ', title)  # Replace multiple spaces with single space
        
        return title
        
    except Exception as e:
        print(f"Error generating podcast title: {str(e)}")
        return None

def generate_summary_title(summary_text: str) -> Optional[str]:
    """
    Generate a clear and descriptive title for a summary.
    
    Args:
        summary_text: The summary text
        
    Returns:
        A title string or None if generation fails
    """
    try:
        if not summary_text or len(summary_text) < 50:
            return None
            
        # Initialize ChatOpenAI
        llm = ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model_name="gpt-3.5-turbo",
            temperature=0.5  # Lower temperature for more focused titles
        )
        
        # Create a prompt for title generation
        # Use only the first ~800 characters of the summary to save tokens
        sample_text = summary_text[:800] if len(summary_text) > 800 else summary_text
        
        prompt = f"""Create a clear, descriptive title for this summary:

        {sample_text}
        
        The title should be:
        - Brief (4-7 words)
        - Factual and informative
        - Represent the main topic or conclusion
        - No quotes or special characters
        
        Return only the title text, nothing else."""
        
        # Generate the title
        response = llm.invoke(prompt)
        
        # Clean the title
        title = response.content.strip()
        title = re.sub(r'^["\'"]|["\'"]$', '', title)  # Remove surrounding quotes
        title = re.sub(r'\s+', ' ', title)  # Replace multiple spaces with single space
        
        return title
        
    except Exception as e:
        print(f"Error generating summary title: {str(e)}")
        return None

def clean_title_for_filename(title: str) -> str:
    """
    Clean a title to make it suitable for use in a filename.
    
    Args:
        title: The title to clean
        
    Returns:
        A cleaned version of the title suitable for filenames
    """
    if not title:
        return ""
        
    # Remove special characters, replace spaces with underscores
    clean = re.sub(r'[^\w\s-]', '', title)
    clean = re.sub(r'\s+', '_', clean)
    
    return clean 