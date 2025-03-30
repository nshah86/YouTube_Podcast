import os
import sys
import streamlit as st
import tempfile
from pathlib import Path
import time
import re
from datetime import datetime

# Add the src directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(current_dir))

# Import settings and utils
try:
    from youtube_podcast.config.settings import OPENAI_API_KEY, DEFAULT_OUTPUT_DIR
except ImportError:
    # Fallback if DEFAULT_OUTPUT_DIR is not defined
    from youtube_podcast.config.settings import OPENAI_API_KEY
    DEFAULT_OUTPUT_DIR = os.path.join(os.getcwd(), "output")
    os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
    
from youtube_podcast.utils.youtube_utils import fetch_transcript
from youtube_podcast.agents.summary_agent import generate_summary
from youtube_podcast.agents.podcast_agent import create_conversation, generate_podcast

# Create output directory if it doesn't exist
os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)

# Page config
st.set_page_config(
    page_title="YouTube Podcast Generator",
    page_icon="🎙️",
    layout="wide"
)

# CSS for styling conversation bubbles
st.markdown("""
<style>
    .chat-container {
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 15px;
        background-color: #f0f2f6;
        max-height: 400px;
        overflow-y: auto;
        border: 1px solid #ddd;
    }
    .message-host1 {
        background-color: #e6f7ff;
        border-radius: 15px 15px 15px 0;
        padding: 10px 15px;
        margin: 10px 20px 10px 0;
        max-width: 80%;
        float: left;
        clear: both;
    }
    .message-host2 {
        background-color: #efefef;
        border-radius: 15px 15px 0 15px;
        padding: 10px 15px;
        margin: 10px 0 10px 20px;
        max-width: 80%;
        float: right;
        clear: both;
    }
    .speaker-name {
        font-weight: bold;
        margin-bottom: 5px;
    }
    .progress-container {
        margin-top: 20px;
        margin-bottom: 20px;
    }
    .progress-step {
        margin-bottom: 10px;
    }
    .audio-container {
        padding: 15px;
        background-color: #f8f9fa;
        border-radius: 10px;
        margin-top: 20px;
        border: 1px solid #ddd;
    }
    .title-card {
        padding: 15px;
        background-color: #e9ecef;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
        border-left: 5px solid #007bff;
    }
</style>
""", unsafe_allow_html=True)

# Check if API key is available
if not OPENAI_API_KEY:
    st.error("⚠️ OPENAI_API_KEY is not set. Please set it in your .env file.")
    st.stop()

# Title and introduction
st.title("🎙️ YouTube Podcast Generator")
st.markdown("""
This tool helps you convert YouTube videos into summaries or podcast-style audio files.
Simply enter a YouTube URL, choose your preferred output type, and let the AI do the rest!
""")

# Function to format conversation for display
def format_conversation_for_display(conversation_text, host1="Host 1", host2="Host 2"):
    """Format the conversation text into HTML for better display"""
    if not conversation_text:
        return ""
    
    # Process the conversation text
    lines = conversation_text.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if line starts with a speaker indicator
        if ':' in line:
            parts = line.split(':', 1)
            speaker = parts[0].strip()
            text = parts[1].strip()
            
            if speaker.lower() in [host1.lower(), host1.split()[0].lower()]:
                formatted_lines.append(f'<div class="message-host1"><div class="speaker-name">{host1}</div>{text}</div>')
            else:
                formatted_lines.append(f'<div class="message-host2"><div class="speaker-name">{host2}</div>{text}</div>')
        else:
            # Lines without a speaker get added as-is
            formatted_lines.append(f'<div class="message-normal">{line}</div>')
    
    return "".join(formatted_lines)

# Sidebar for inputs
with st.sidebar:
    st.header("Input Options")
    youtube_url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
    
    output_type = st.radio(
        "Output Type",
        ["summary", "podcast"],
        help="Choose between a text summary or an audio podcast"
    )
    
    if output_type == "podcast":
        gender = st.radio(
            "Voice Gender",
            ["male", "female"],
            help="Choose the voice gender for your podcast"
        )
    else:
        gender = "mixed"  # Default value
    
    process_button = st.button("Process Video", type="primary")

# Main content area
if process_button and youtube_url:
    # Create a basic state dictionary
    state = {
        "url": youtube_url,
        "transcript": "",
        "summary": "",
        "summary_title": "",
        "summary_filename": "",
        "conversation": "",
        "podcast_title": "",
        "podcast_filename": "",
        "audio_path": "",
        "gender": gender,
        "output_type": output_type,
        "status": "initialized",
        "error": None,
        "start_time": datetime.now().isoformat(),
    }
    
    # Create progress tracking container
    progress_container = st.container()
    with progress_container:
        st.subheader("Processing Progress")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Step 1: Fetch transcript
        status_text.info("Step 1/3: Fetching YouTube transcript...")
        
        try:
            # Show spinner during transcript fetch
            with st.spinner():
                # Fetch transcript
                transcript_text = fetch_transcript(youtube_url)
                
            if transcript_text:
                state["transcript"] = transcript_text
                state["status"] = "transcript_fetched"
                progress_bar.progress(33)
                with st.expander("View Transcript"):
                    st.text_area("Video Transcript", transcript_text[:1000] + "..." if len(transcript_text) > 1000 else transcript_text, height=200)
            else:
                status_text.error("❌ Failed to fetch transcript")
                st.stop()
        except Exception as e:
            status_text.error(f"❌ Error fetching transcript: {str(e)}")
            st.stop()
        
        # Step 2: Generate output based on selected type
        if output_type == "summary":
            status_text.info("Step 2/3: Generating summary...")
            try:
                # Generate summary with spinner
                with st.spinner():
                    summary_result = generate_summary(state)
                    state.update(summary_result)
                
                if state.get("summary"):
                    state["status"] = "summary_generated"
                    progress_bar.progress(66)
                else:
                    status_text.error("❌ Failed to generate summary")
                    st.stop()
            except Exception as e:
                status_text.error(f"❌ Error generating summary: {str(e)}")
                st.stop()
                
            # Step 3: Display summary result
            status_text.info("Step 3/3: Processing complete!")
            progress_bar.progress(100)
            
            # Show the summary
            st.header("📝 Summary Generated")
            st.markdown(f"## {state.get('summary_title', 'Summary')}")
            st.markdown(state.get("summary", ""))
            
            # Offer download option
            if state.get("summary_filename"):
                summary_path = os.path.join(DEFAULT_OUTPUT_DIR, state.get("summary_filename"))
                with open(summary_path, "r", encoding="utf-8") as f:
                    summary_content = f.read()
                    
                st.download_button(
                    label="Download Summary as Text",
                    data=summary_content,
                    file_name=state.get("summary_filename"),
                    mime="text/plain"
                )
        
        elif output_type == "podcast":
            # Step 2: Generate conversation
            status_text.info("Step 2/3: Generating podcast conversation...")
            try:
                # Generate conversation with spinner
                with st.spinner():
                    conversation_result = create_conversation(state)
                    state.update(conversation_result)
                
                if state.get("conversation"):
                    state["status"] = "conversation_generated"
                    progress_bar.progress(66)
                    
                    # Show the conversation
                    st.header("💬 Podcast Conversation")
                    st.markdown(f"## {state.get('podcast_title', 'Podcast Conversation')}")
                    
                    # Display formatted conversation
                    conversation_html = format_conversation_for_display(
                        state.get("conversation", ""), 
                        host1="Jake" if gender == "male" else "Sarah",
                        host2="Michael" if gender == "male" else "Emma"
                    )
                    st.markdown(f'<div class="chat-container">{conversation_html}</div>', unsafe_allow_html=True)
                else:
                    status_text.error("❌ Failed to generate conversation")
                    st.stop()
            except Exception as e:
                status_text.error(f"❌ Error generating conversation: {str(e)}")
                st.stop()
            
            # Step 3: Generate audio podcast
            status_text.info("Step 3/3: Generating audio podcast...")
            try:
                # Generate podcast with spinner
                with st.spinner():
                    podcast_result = generate_podcast(state)
                    state.update(podcast_result)
                
                if state.get("audio_path"):
                    state["status"] = "podcast_generated"
                    progress_bar.progress(100)
                    
                    # Show the audio file
                    st.header("🎧 Podcast Generated")
                    
                    # Display audio player
                    audio_path = state.get("audio_path")
                    st.audio(audio_path)
                    
                    # Offer download option for audio
                    with open(audio_path, "rb") as f:
                        audio_data = f.read()
                        
                    st.download_button(
                        label="Download Podcast Audio",
                        data=audio_data,
                        file_name=os.path.basename(audio_path),
                        mime="audio/mpeg"
                    )
                    
                    # Processing complete
                    status_text.success("✅ Podcast generated successfully!")
                else:
                    status_text.error("❌ Failed to generate podcast audio")
                    st.stop()
            except Exception as e:
                status_text.error(f"❌ Error generating podcast audio: {str(e)}")
                st.stop()

# Display instructions when no URL is entered
else:
    st.info("👈 Enter a YouTube URL in the sidebar and choose your preferred output type to get started!")
    
    # Example section
    st.subheader("How to use this tool")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Summary Option")
        st.markdown("""
        - Provides a concise text summary of the video
        - Captures the key points and main ideas
        - Useful for quickly understanding content
        """)
    
    with col2:
        st.markdown("### Podcast Option")
        st.markdown("""
        - Creates a conversational podcast from the video
        - Features two hosts discussing the content
        - Available in male or female voices
        - Downloadable as an MP3 file
        """)

# Footer
st.markdown("---")
st.markdown("Built with Streamlit, LangChain, and LangGraph 🚀") 