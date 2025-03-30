import os
import sys
import streamlit as st
import tempfile
from pathlib import Path

# Add the src directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(current_dir))

from youtube_podcast.models.state import AgentState
from youtube_podcast.config.settings import OPENAI_API_KEY, DEFAULT_OUTPUT_FILENAME
from youtube_podcast.utils.youtube_utils import fetch_transcript
from youtube_podcast.agents.summary_agent import generate_summary
from youtube_podcast.agents.podcast_agent import create_conversation, generate_podcast

# Page config
st.set_page_config(
    page_title="YouTube Podcast Generator",
    page_icon="🎙️",
    layout="wide"
)

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
    with st.spinner("Processing... Please wait"):
        # Create initial state
        state = AgentState(
            url=youtube_url,
            transcript="",
            summary="",
            conversation="",
            audio_path="",
            output_type=output_type,
            gender=gender,
            status="initialized",
            error=None
        )
        
        # Step 1: Fetch transcript
        st.subheader("Step 1: Fetching Transcript")
        progress_bar = st.progress(25)
        
        try:
            # Fetch transcript
            transcript_text = fetch_transcript(youtube_url)
            if transcript_text:
                state["transcript"] = transcript_text
                state["status"] = "transcript_fetched"
                st.success("✅ Transcript fetched successfully")
                st.expander("View Transcript").text(transcript_text[:1000] + "..." if len(transcript_text) > 1000 else transcript_text)
            else:
                st.error("❌ Failed to fetch transcript")
                st.stop()
        except Exception as e:
            st.error(f"❌ Error fetching transcript: {str(e)}")
            st.stop()
        
        progress_bar.progress(50)
        
        # Step 2: Generate output based on selected type
        if output_type == "summary":
            st.subheader("Step 2: Generating Summary")
            try:
                # Generate summary
                state = generate_summary(state)
                if state["status"] == "summary_generated":
                    progress_bar.progress(100)
                    st.success("✅ Summary generated successfully")
                    
                    # Display the summary title and filename
                    st.markdown(f"### {state['summary_title']}")
                    st.caption(f"Saved as: {state['summary_filename']}")
                    
                    # Display the summary in a nice box
                    st.markdown(f"<div style='background-color:#f0f2f6;padding:20px;border-radius:10px'>{state['summary']}</div>", unsafe_allow_html=True)
                    
                    # Add download button for the summary text file
                    with open(state["summary_filename"], "r", encoding='utf-8') as file:
                        st.download_button(
                            label="Download Summary Text",
                            data=file,
                            file_name=state["summary_filename"],
                            mime="text/plain"
                        )
                else:
                    st.error(f"❌ {state.get('error', 'Error generating summary')}")
            except Exception as e:
                st.error(f"❌ Error generating summary: {str(e)}")
        
        else:  # podcast
            st.subheader("Step 2: Creating Conversation")
            try:
                # Generate conversation
                state = create_conversation(state)
                if state["status"] == "conversation_created":
                    progress_bar.progress(75)
                    st.success("✅ Conversation script created")
                    
                    # Show podcast title
                    st.markdown(f"### {state['podcast_title']}")
                    
                    # Show conversation script
                    with st.expander("View Conversation Script"):
                        st.markdown(state["conversation"])
                    
                    # Generate podcast
                    st.subheader("Step 3: Generating Podcast Audio")
                    state = generate_podcast(state)
                    
                    if state["status"] == "podcast_generated":
                        progress_bar.progress(100)
                        st.success("✅ Podcast generated successfully")
                        
                        # Display filename
                        st.caption(f"Saved as: {state['audio_path']}")
                        
                        # Display audio player
                        audio_file = open(state["audio_path"], "rb")
                        st.audio(audio_file.read(), format="audio/mp3")
                        
                        # Provide download button
                        with open(state["audio_path"], "rb") as file:
                            btn = st.download_button(
                                label="Download Podcast",
                                data=file,
                                file_name=state["audio_path"],
                                mime="audio/mp3"
                            )
                    else:
                        st.error(f"❌ {state.get('error', 'Error generating podcast audio')}")
                else:
                    st.error(f"❌ {state.get('error', 'Error creating conversation')}")
            except Exception as e:
                st.error(f"❌ Error in podcast generation: {str(e)}")

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