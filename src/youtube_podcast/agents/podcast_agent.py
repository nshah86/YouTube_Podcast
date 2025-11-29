from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from gtts import gTTS
from ..config.settings import OPENAI_API_KEY, DEFAULT_LLM_MODEL, DEFAULT_LANGUAGE_CODE, DEFAULT_OUTPUT_FILENAME, DEFAULT_OUTPUT_DIR
from ..utils.eleven_labs import text_to_speech
from ..utils.title_generator import generate_podcast_title
import os
import re
import time
import random
import tempfile
import shutil
from datetime import datetime
from typing import Dict, Optional, List

# Set environment variables
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

def create_conversation(state: Dict) -> Dict:
    """Generate a conversation between two hosts based on a YouTube transcript"""
    if state["status"] != "transcript_fetched":
        state["error"] = "No transcript available"
        return state
    
    # Setup the LLM
    llm = ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        model_name="gpt-3.5-turbo",
        temperature=0.7
    )
    
    # Define the prompt templates
    system_prompt = """You are an AI assistant tasked with creating a podcast-style conversation
    between two hosts about a YouTube video.

    The conversation should:
    - Be engaging and flow naturally between two hosts
    - Include a back-and-forth discussion format with clear speaker indications
    - Cover the main points from the transcript in an informative way
    - Be accessible to a general audience
    - Use a conversational tone with natural language patterns
    - Avoid overly formal language or academic phrasing
    - Include some filler words and speech patterns (like "you know", "I think", "well")
    - End with a conclusion or call to action
    - Keep the total length between 700-1200 words
    
    For EACH line of dialogue, start with the speaker name followed by a colon.
    For example:
    Host1: Hello and welcome to our podcast!
    Host2: Today we're discussing an interesting topic...
    
    Alternate between Host1 and Host2 throughout the conversation.
    
    IMPORTANT GUIDELINES:
    - Avoid using asterisks, parentheses or special characters
    - Write as people actually speak, not as they write
    - Use contractions (don't, I'm, we're) as people naturally do in conversation
    - Occasionally include short questions or brief responses
    - Vary sentence length for a more natural cadence
    """
    
    human_prompt = """Here is a transcript from a YouTube video:
    
    {transcript}
    
    Based on this transcript, create an engaging podcast conversation between two hosts.
    Make it sound like a natural conversation between friends, not a formal discussion.
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
    
    # Generate the conversation
    transcript = state["transcript"]
    ai_message = generation_chain.invoke(transcript)
    conversation = ai_message.content
    
    # Process conversation to ensure proper format
    formatted_conversation = format_conversation(conversation)
    
    # Generate title for the podcast
    podcast_title = generate_podcast_title(formatted_conversation)
    
    # Create a suitable filename
    if podcast_title:
        # Clean title to use as filename (remove special chars, replace spaces with underscores)
        clean_title = ''.join(c if c.isalnum() or c in ' -_' else '_' for c in podcast_title)
        clean_title = clean_title.replace(' ', '_')
        podcast_filename = f"{clean_title}.mp3"
    else:
        # Fallback to date-based filename
        current_date = datetime.now().strftime("%Y%m%d")
        podcast_filename = f"podcast_{current_date}.mp3"
    
    # Update the state
    state["conversation"] = formatted_conversation
    state["podcast_title"] = podcast_title
    state["podcast_filename"] = podcast_filename
    state["status"] = "conversation_created"
    
    return state

def format_conversation(conversation: str) -> str:
    """Format the conversation to ensure proper speaker labeling and alternation"""
    lines = conversation.strip().split('\n')
    formatted_lines = []
    current_speaker = None
    
    # Define possible host names for consistent replacement
    host1_options = ["Host1", "Host 1", "Speaker1", "Speaker 1"]
    host2_options = ["Host2", "Host 2", "Speaker2", "Speaker 2"]
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if line starts with a speaker indicator
        if ':' in line:
            parts = line.split(':', 1)
            speaker = parts[0].strip()
            text = parts[1].strip()
            
            # Normalize speaker names for consistency
            speaker_lower = speaker.lower()
            if any(option.lower() in speaker_lower for option in host1_options):
                speaker = "Host1"
            elif any(option.lower() in speaker_lower for option in host2_options):
                speaker = "Host2"
                
            current_speaker = speaker
            formatted_lines.append(f"{speaker}: {text}")
        else:
            # For lines without speaker prefixes, assign to alternating speakers
            if current_speaker is None or current_speaker == "Host2":
                current_speaker = "Host1"
            else:
                current_speaker = "Host2"
            formatted_lines.append(f"{current_speaker}: {line}")
    
    return '\n'.join(formatted_lines)

def generate_podcast(state: Dict) -> Dict:
    """Generate the podcast audio file from a conversation script"""
    max_retries = 3
    retry_delay = 2  # Initial delay in seconds
    
    if state["status"] != "conversation_created" or "conversation" not in state:
        state["error"] = "No conversation script available"
        return state
    
    # Get gender from state or default to mixed
    gender = state.get("gender", "mixed")
    
    # Create temporary directory for audio file to avoid permission issues
    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_audio_path = os.path.join(tmp_dir, "temp_podcast.mp3")
        
        # Create output directory if it doesn't exist
        os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
        
        # Determine the final audio path
        if "podcast_filename" in state and state["podcast_filename"]:
            audio_filename = state["podcast_filename"]
        else:
            # Fallback to date-based filename
            current_date = datetime.now().strftime("%Y%m%d")
            audio_filename = f"podcast_{current_date}.mp3"
        
        audio_path = os.path.join(DEFAULT_OUTPUT_DIR, audio_filename)
        
        # Retry logic for audio generation
        for attempt in range(max_retries):
            try:
                # Call the text_to_speech function
                text_to_speech(
                    text=state["conversation"],
                    output_file=temp_audio_path,
                    gender=gender
                )
                
                # If successful, copy from temp location to final destination
                if os.path.exists(temp_audio_path):
                    shutil.copy2(temp_audio_path, audio_path)
                    break  # Exit the retry loop on success
                else:
                    raise Exception(f"Failed to generate audio file (attempt {attempt+1}/{max_retries})")
                    
            except Exception as e:
                if attempt < max_retries - 1:  # If not the last attempt
                    # Exponential backoff with jitter
                    sleep_time = retry_delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f"Audio generation failed (attempt {attempt+1}/{max_retries}): {str(e)}. Retrying in {sleep_time:.1f} seconds...")
                    time.sleep(sleep_time)
                else:
                    # Last attempt failed
                    state["error"] = f"Failed to generate audio after {max_retries} attempts: {str(e)}"
                    return state
        
        # Update the state with audio path
        state["audio_path"] = audio_path
        state["status"] = "podcast_generated"
    
    return state
