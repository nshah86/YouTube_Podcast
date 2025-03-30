import os
import sys
import streamlit as st
import tempfile
from pathlib import Path
import time
import re


current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(current_dir))

from youtube_podcast.config.settings import OPENAI_API_KEY, DEFAULT_OUTPUT_DIR
from youtube_podcast.utils.youtube_utils import fetch_transcript
from youtube_podcast.agents.summary_agent import generate_summary
from youtube_podcast.agents.podcast_agent import create_conversation, generate_podcast
from youtube_podcast.workflow import initialize_state

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
        gender = None
    
    process_button = st.button("Process Video", type="primary")

# Main content area
if process_button and youtube_url:
    # Create initial state
    state = initialize_state()
    state["url"] = youtube_url
    state["output_type"] = output_type
    state["gender"] = gender
    
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
                    state = generate_summary(state)
                
                if state["status"] == "summary_generated":
                    progress_bar.progress(100)
                    status_text.success("✅ Processing complete!")
                    
                    # Create a container for the summary output
                    summary_container = st.container()
                    with summary_container:
                        # Display the summary title in a nice card
                        st.markdown(f"""
                        <div class="title-card">
                            <h2>{state['summary_title']}</h2>
                            <p>Summary generated from YouTube video</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.caption(f"Saved as: {state['summary_filename']}")
                        
                        # Display the summary in a nice box
                        st.markdown(f"<div style='background-color:#f0f2f6;padding:20px;border-radius:10px'>{state['summary']}</div>", unsafe_allow_html=True)
                        
                        # Add download button for the summary text file
                        with open(state["summary_filename"], "r", encoding='utf-8') as file:
                            st.download_button(
                                label="📥 Download Summary Text",
                                data=file,
                                file_name=state["summary_filename"],
                                mime="text/plain"
                            )
                else:
                    status_text.error(f"❌ {state.get('error', 'Error generating summary')}")
            except Exception as e:
                status_text.error(f"❌ Error generating summary: {str(e)}")
        
        else:  # podcast
            status_text.info("Step 2/3: Creating conversation script...")
            try:
                # Generate conversation with spinner
                with st.spinner():
                    state = create_conversation(state)
                
                if state["status"] == "conversation_created":
                    progress_bar.progress(66)
                    
                    # Create a container for the podcast output
                    podcast_container = st.container()
                    with podcast_container:
                        # Display the podcast title in a nice card
                        st.markdown(f"""
                        <div class="title-card">
                            <h2>{state['podcast_title']}</h2>
                            <p>Podcast conversation between hosts</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Extract host names based on gender preference
                        if state.get("gender") == "male":
                            host1, host2 = "Michael", "David"
                        elif state.get("gender") == "female":
                            host1, host2 = "Sarah", "Emily"
                        else:
                            host1, host2 = "Alex", "Jamie"
                            
                        # Show conversation script as a chat
                        st.subheader("Conversation Script")
                        st.markdown('<div class="chat-container">' + 
                                   format_conversation_for_display(state["conversation"], host1, host2) + 
                                   '<div style="clear:both"></div></div>', 
                                   unsafe_allow_html=True)
                    
                    # Generate podcast
                    status_text.info("Step 3/3: Generating podcast audio...")
                    with st.spinner("Creating audio file... this may take a moment"):
                        # Add artificial delay for better UX with progress bar animation
                        for percent in range(67, 95, 5):
                            time.sleep(0.5)
                            progress_bar.progress(percent)
                        
                        state = generate_podcast(state)
                    
                    if state["status"] == "podcast_generated":
                        progress_bar.progress(100)
                        status_text.success("✅ Processing complete!")
                        
                        with podcast_container:
                            # Display filename and audio player
                            st.markdown(f'<div class="audio-container">', unsafe_allow_html=True)
                            st.caption(f"Audio file saved as: {os.path.basename(state['audio_path'])}")
                            
                            # Add info about natural conversation
                            st.info("The audio uses natural speech patterns and conversational style for a more engaging listening experience.")
                            
                            # Display audio player with waveform and controls
                            try:
                                audio_file = open(state["audio_path"], "rb")
                                audio_bytes = audio_file.read()
                                audio_file.close()
                                
                                st.audio(audio_bytes, format="audio/mp3")
                                
                                # Add download button
                                st.download_button(
                                    label="📥 Download Podcast MP3",
                                    data=audio_bytes,
                                    file_name=os.path.basename(state["audio_path"]),
                                    mime="audio/mp3"
                                )
                            except Exception as e:
                                st.error(f"Error loading audio: {str(e)}")
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        status_text.error(f"❌ {state.get('error', 'Error generating podcast audio')}")
                else:
                    status_text.error(f"❌ {state.get('error', 'Error creating conversation')}")
            except Exception as e:
                status_text.error(f"❌ Error in podcast generation: {str(e)}")

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