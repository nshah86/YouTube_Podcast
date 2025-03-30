# YouTube Podcast Generator

A modular application with a Streamlit UI that converts YouTube videos into text summaries or podcast-style audio conversations.

## Features

- Extract transcripts from any YouTube video
- Generate concise text summaries
- Create podcast-style conversations between two hosts
- Choose male or female voice personas for podcast generation
- Beautiful Streamlit UI for easy interaction
- Download audio files directly from the browser

## Screenshots

(Coming soon)

## Installation

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your API keys:
   ```
   OPENAI_API_KEY="your_openai_api_key"
   ```

## Usage

Run the application with:

```
python src/main.py
```

This will launch the Streamlit web interface where you can:
1. Enter a YouTube URL
2. Choose between summary or podcast output
3. Select voice preferences (for podcast)
4. Process the video and view/download the results

Alternatively, you can run the Streamlit app directly:

```
streamlit run src/app.py
```

## Project Structure

The project follows a modular architecture:

- `src/youtube_podcast/agents/`: Contains agents for transcript, summary, and podcast generation
- `src/youtube_podcast/models/`: Data models for the application state
- `src/youtube_podcast/utils/`: Utility functions for YouTube processing
- `src/youtube_podcast/config/`: Configuration settings and environment variables
- `src/youtube_podcast/workflow.py`: LangGraph workflow definition
- `src/app.py`: Streamlit user interface
- `src/main.py`: Main entry point for the application

## Requirements

- Python 3.8+
- OpenAI API key
- Internet connection for accessing YouTube videos 