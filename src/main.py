#!/usr/bin/env python3
import os
import sys
import subprocess
import importlib.util
from typing import Dict

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from youtube_podcast.config.settings import OPENAI_API_KEY
from youtube_podcast.workflow import initialize_state

def check_config():
    """Check if the necessary configuration is set up."""
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY is not set. Please set it in your .env file.")
        return False
    return True

def is_streamlit_installed():
    """Check if streamlit is installed."""
    return importlib.util.find_spec("streamlit") is not None

def launch_streamlit():
    """Launch the Streamlit app."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(script_dir, "app.py")
    
    # Check if the app file exists
    if not os.path.exists(app_path):
        print(f"Error: Could not find app file at {app_path}")
        print(f"Current directory: {os.getcwd()}")
        print(f"Script directory: {script_dir}")
        return False
    
    # Try to run streamlit
    try:
        # First, check if streamlit is installed
        if not is_streamlit_installed():
            print("Error: Streamlit does not appear to be installed.")
            print("Please install streamlit with: pip install streamlit")
            return False
        
        # Try using Python module directly if streamlit command might not be in PATH
        print(f"Starting Streamlit app at {app_path}...")
        print("To view the app, open your browser at http://localhost:8501")
        
        # Look for streamlit in the common Python scripts locations
        streamlit_paths = [
            r"C:\Users\Neel_Learn\AppData\Roaming\Python\Python313\Scripts\streamlit.exe",
            os.path.join(os.path.dirname(sys.executable), "Scripts", "streamlit.exe"),
            r"C:\Users\Neel_Learn\AppData\Local\Programs\Python\Python313\Scripts\streamlit.exe"
        ]
        
        streamlit_cmd = None
        for path in streamlit_paths:
            if os.path.exists(path):
                streamlit_cmd = path
                print(f"Found Streamlit at: {streamlit_cmd}")
                break
        
        try:
            if streamlit_cmd:
                # Use the full path to streamlit
                subprocess.run([streamlit_cmd, "run", app_path], check=True)
            else:
                # Try using streamlit as a module
                python_exe = sys.executable
                print(f"Using Python from: {python_exe}")
                result = subprocess.run([python_exe, "-m", "streamlit", "run", app_path], 
                                      check=True, 
                                      capture_output=True, 
                                      text=True)
                print(result.stdout)
                if result.stderr:
                    print(f"Warning: {result.stderr}")
            return True
        except subprocess.SubprocessError as e:
            print(f"Subprocess error: {str(e)}")
            # Last attempt - try launching with python -m directly
            python_exe = sys.executable
            try:
                result = subprocess.run([python_exe, "-m", "streamlit", "run", app_path], 
                                      check=False,  # Don't raise exception
                                      capture_output=True,
                                      text=True)
                if result.returncode != 0:
                    print(f"Error output: {result.stderr}")
                    raise Exception(f"Failed to start streamlit. Return code: {result.returncode}")
                return True
            except Exception as inner_e:
                print(f"Failed to launch with python -m streamlit: {str(inner_e)}")
                raise
            
        return True
    except KeyboardInterrupt:
        print("\nApplication closed.")
        return True
    except Exception as e:
        print(f"Error launching Streamlit: {str(e)}")
        print("\nAlternative: Try running the app directly with:")
        print(f"  {sys.executable} -m streamlit run {app_path}")
        print("\nOr run the app directly:")
        print(f"  {sys.executable} {app_path}")
        return False

def main():
    """Main entry point for the application."""
    print("==== YouTube Podcast Generator ====")
    print("This tool will help you convert YouTube videos to summaries or podcasts.")
    print("-----------------------------------")
    
    # Check if configuration is valid
    if not check_config():
        return
    
    # Launch the Streamlit app
    if not launch_streamlit():
        print("\nFallback: Running the app directly.")
        try:
            # Try to run the direct_run.py script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            direct_run_path = os.path.join(script_dir, "direct_run.py")
            
            if os.path.exists(direct_run_path):
                print(f"Running direct launcher: {direct_run_path}")
                python_exe = sys.executable
                subprocess.run([python_exe, direct_run_path], check=True)
            else:
                # Direct fallback to importing the app module
                print("Direct launcher not found. Attempting to import app directly.")
                app_path = os.path.join(script_dir, "app.py")
                
                sys.path.insert(0, script_dir)
                print("Press Ctrl+C to exit when done.")
                
                # Import the app module directly
                import app
                print("App module imported directly.")
        except Exception as e:
            print(f"Error running app directly: {str(e)}")
            print("\nPlease try one of these methods:")
            print(f"1. {sys.executable} -m streamlit run {os.path.join(script_dir, 'app.py')}")
            print(f"2. {sys.executable} {os.path.join(script_dir, 'direct_run.py')}")
            print(f"3. Make sure Streamlit is installed: pip install streamlit")

if __name__ == "__main__":
    main()
