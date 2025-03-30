#!/usr/bin/env python3
import os
import sys
import subprocess

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from youtube_podcast.config.settings import OPENAI_API_KEY
from youtube_podcast.models.state import AgentState

def check_config():
    """Check if the necessary configuration is set up."""
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY is not set. Please set it in your .env file.")
        return False
    return True

def launch_streamlit():
    """Launch the Streamlit app."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(script_dir, "app.py")
    
    try:
        subprocess.run(["streamlit", "run", app_path])
    except KeyboardInterrupt:
        print("\nApplication closed.")
    except Exception as e:
        print(f"An error occurred while launching the app: {e}")

def initialize_state():
    """Initialize the AgentState with default values."""
    return AgentState(
        url="",
        transcript="",
        summary="",
        summary_title=None,
        summary_filename=None,
        conversation="",
        podcast_title=None,
        audio_path="",
        output_type="",
        gender=None,
        status="initialized",
        error=None
    )

def main():
    """Main entry point for the application."""
    print("==== YouTube Podcast Generator ====")
    print("This tool will help you convert YouTube videos to summaries or podcasts.")
    print("-----------------------------------")
    
    # Check if configuration is valid
    if not check_config():
        return
    
    # Launch the Streamlit app
    launch_streamlit()

if __name__ == "__main__":
    main()
