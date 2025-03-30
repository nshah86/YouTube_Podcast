import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT")
USER_AGENT = os.getenv("USER_AGENT")
HF_TOKEN = os.getenv("HF_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# LLM Settings
DEFAULT_LLM_MODEL = "gpt-4o"

# Debug Settings
DEBUG_LANGGRAPH = False
DEBUG_LANGGRAPH_PORT = 8000

# Output Settings
DEFAULT_OUTPUT_FILENAME = "YT_podcast.mp3"
DEFAULT_LANGUAGE_CODE = 'en'
