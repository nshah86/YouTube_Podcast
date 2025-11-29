import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT")
USER_AGENT = os.getenv("USER_AGENT")
HF_TOKEN = os.getenv("HF_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")

# LLM Settings
DEFAULT_LLM_MODEL = "gpt-4o"

# Debug Settings
DEBUG_LANGGRAPH = False
DEBUG_LANGGRAPH_PORT = 8000

# Output Settings
DEFAULT_OUTPUT_DIR = os.path.join(os.getcwd(), "output")
DEFAULT_OUTPUT_FILENAME = "YT_podcast.mp3"

# Audio settings
DEFAULT_SPEECH_MODEL = "tts-1"  # OpenAI TTS model

# Create output directory if it doesn't exist
os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)

# Default language for text-to-speech
DEFAULT_LANGUAGE_CODE = "en"
