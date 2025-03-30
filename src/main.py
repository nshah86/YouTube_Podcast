#!/usr/bin/env python3
import os
from youtube_podcast.workflow import run_workflow
from youtube_podcast.config.settings import OPENAI_API_KEY

def check_config():
    """Check if the necessary configuration is set up."""
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY is not set. Please set it in your .env file.")
        return False
    return True

def main():
    """Main entry point for the application."""
    print("==== YouTube Podcast Generator ====")
    print("This tool will help you convert YouTube videos to summaries or podcasts.")
    print("-----------------------------------")
    
    # Check if configuration is valid
    if not check_config():
        return
    
    # Ask user if they want to enable debug mode
    debug_mode = False
    debug_choice = input("Enable debug visualization? (yes/no): ").lower().strip()
    if debug_choice in ["yes", "y", "true"]:
        debug_mode = True
        print("Debug visualization enabled. You will be able to see the workflow graph in your browser.")
    
    # Run the workflow
    try:
        run_workflow(debug=debug_mode)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()
