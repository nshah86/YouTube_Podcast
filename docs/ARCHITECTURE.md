# Architecture Overview

## Agent-Based Architecture

This application uses **multiple LangGraph agents** for processing YouTube content:

### Agents

1. **Transcript Agent** (`src/youtube_podcast/agents/transcript_agent.py`)
   - Fetches YouTube video transcripts
   - Handles URL validation
   - Manages transcript state
   - Functions: `get_url_input()`, `fetch_transcript()`, `update_transcript_in_state()`

2. **Summary Agent** (`src/youtube_podcast/agents/summary_agent.py`)
   - Generates AI-powered summaries using OpenAI GPT
   - Creates formatted summary documents
   - Generates summary titles
   - Function: `generate_summary()`

3. **Podcast Agent** (`src/youtube_podcast/agents/podcast_agent.py`)
   - Creates conversational podcasts between two hosts
   - Generates audio with text-to-speech (gTTS)
   - Manages voice selection (male/female)
   - Functions: `create_conversation()`, `generate_podcast()`

### Workflow Graph

The `workflow.py` file defines a LangGraph StateGraph that orchestrates these agents:

```
START
  ↓
get_url_node (Transcript Agent)
  ↓
fetch_transcript_node (Transcript Agent)
  ↓
get_preferences_node (Transcript Agent)
  ↓
    ├─→ summary_node (Summary Agent) → END
    └─→ conversation_node (Podcast Agent)
            ↓
        podcast_node (Podcast Agent) → END
```

### Current Implementation

**Direct Agent Calls**: Currently, Flask routes call agents directly for simplicity:
- `/extract` → `fetch_transcript()`
- `/generate-summary` → `generate_summary()`
- `/generate-podcast` → `generate_podcast()`

**Workflow Available**: The full LangGraph workflow is available in `workflow.py` and can be integrated for more complex orchestration.

### State Management

All agents use a shared state dictionary (`AgentState`) that includes:
- `url`: YouTube video URL
- `transcript`: Extracted transcript text
- `summary`: Generated summary
- `conversation`: Podcast dialogue
- `status`: Current processing status
- `error`: Error messages if any

## Database Architecture

### Supabase Integration

- **User Authentication**: Supabase Auth
- **User Profiles**: `user_profiles` table
- **API Tokens**: `api_tokens` table (linked to users)
- **Usage History**: `usage_history` table

### API Token Management

- Tokens stored in Supabase database
- In-memory cache for performance
- Automatic sync between cache and database
- User-specific token limits based on plan

## File Structure

```
VideoTranscript Pro/
├── app.py                 # Main Flask application
├── config.py              # Configuration management
├── run.py                 # WSGI entry point
├── src/
│   └── youtube_podcast/
│       ├── agents/        # LangGraph agents
│       ├── models/        # Data models
│       ├── utils/         # Utilities
│       ├── config/        # Settings
│       └── workflow.py    # LangGraph workflow
├── templates/             # HTML templates
├── static/                # CSS, JS, images
├── tests/                 # Test suite
└── docs/                  # Documentation
```

## Data Flow

1. User submits YouTube URL
2. Transcript Agent extracts transcript
3. User chooses: Summary or Podcast
4. Respective agent processes the transcript
5. Results saved to output directory
6. Usage tracked in Supabase

