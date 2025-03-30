# YouTube Podcast Generator

A modular agentic workflow application that converts YouTube videos into text summaries or podcast-style audio conversations.

## Features

- Extract transcripts from any YouTube video
- Generate concise text summaries
- Create podcast-style conversations between two hosts
- Choose male or female voice personas for podcast generation
- Debug visualization of the workflow graph using LangGraph

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

Follow the interactive prompts to:
1. Enter a YouTube URL
2. Choose between summary or podcast output
3. Select voice preferences (for podcast)
4. Enable debug visualization if desired

## Debug Visualization

When debug mode is enabled, you can view the LangGraph workflow visualization by opening:
```
http://localhost:8000
```

This will show a real-time visualization of the agent workflow as it progresses.

## Project Structure

The project follows a modular architecture:

- `src/youtube_podcast/agents/`: Contains agents for transcript, summary, and podcast generation
- `src/youtube_podcast/models/`: Data models for the application state
- `src/youtube_podcast/utils/`: Utility functions for YouTube processing
- `src/youtube_podcast/config/`: Configuration settings and environment variables
- `src/youtube_podcast/workflow.py`: LangGraph workflow definition
- `src/main.py`: Main entry point for the application

## Requirements

- Python 3.8+
- OpenAI API key
- Internet connection for accessing YouTube videos 