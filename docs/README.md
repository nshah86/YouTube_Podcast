# VideoTranscript Pro - Complete Documentation

A production-ready web application for extracting YouTube transcripts, generating AI summaries, and creating podcast audio.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Features](#features)
5. [API Documentation](#api-documentation)
6. [Architecture](#architecture)
7. [Database Setup](#database-setup)
8. [Deployment](#deployment)
9. [Testing](#testing)
10. [Production Checklist](#production-checklist)

---

## Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key
- Supabase account (for user authentication)
- Internet connection

### 5-Minute Setup

```bash
# 1. Clone and navigate to project
cd Youtube_Podcast

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
# Windows:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create .env file
cp .env.example .env
# Edit .env with your API keys

# 6. Run the application
python start.py
```

Visit `http://127.0.0.1:5000` in your browser.

---

## Installation

### Step-by-Step Installation

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd Youtube_Podcast
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   Create a `.env` file in the project root:
   ```env
   # Required
   OPENAI_API_KEY=your_openai_api_key
   SECRET_KEY=your_secure_random_secret_key
   
   # Supabase (for authentication)
   REACT_APP_SUPABASE_URL=https://your-project.supabase.co
   REACT_APP_SUPABASE_ANON_KEY=your_anon_key
   
   # Optional
   APP_ENV=development
   LOG_LEVEL=INFO
   ```

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | Your OpenAI API key for AI features |
| `SECRET_KEY` | Yes | Flask secret key (use a strong random string) |
| `REACT_APP_SUPABASE_URL` | Yes* | Supabase project URL |
| `REACT_APP_SUPABASE_ANON_KEY` | Yes* | Supabase anonymous key |
| `APP_ENV` | No | Environment: `development`, `testing`, or `production` |
| `LOG_LEVEL` | No | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

*Required for user authentication features

### Generate Secret Key

```python
import secrets
print(secrets.token_urlsafe(32))
```

---

## Features

### Core Features

- ✅ **Transcript Extraction** - Extract transcripts from any public YouTube video
- ✅ **AI Summarization** - Generate comprehensive summaries using GPT
- ✅ **Podcast Generation** - Create podcast conversations with audio
- ✅ **Bulk Processing** - Process multiple videos at once
- ✅ **CSV Import/Export** - Import URLs from CSV, export results
- ✅ **User Accounts** - Sign up, login, manage account
- ✅ **Usage Tracking** - Track all operations and token usage
- ✅ **API Access** - RESTful API with authentication
- ✅ **Dark/Light Mode** - Theme switching

### Feature Comparison

See [FEATURES.md](FEATURES.md) for detailed comparison with youtube-transcript.io.

---

## API Documentation

### Authentication

All API endpoints (except public ones) require authentication:

```bash
Authorization: Basic <your-api-token>
```

Generate API tokens from your account dashboard after logging in.

### Endpoints

#### Extract Transcript
```http
POST /extract
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

#### Generate Summary
```http
POST /generate-summary
Content-Type: application/json

{
  "transcript": "transcript text...",
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

#### Generate Podcast
```http
POST /generate-podcast
Content-Type: application/json

{
  "transcript": "transcript text...",
  "gender": "male",
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

#### Bulk Extract
```http
POST /bulk-extract
Content-Type: application/json

{
  "urls": [
    "https://www.youtube.com/watch?v=VIDEO_ID_1",
    "https://www.youtube.com/watch?v=VIDEO_ID_2"
  ]
}
```

#### API Transcripts (Authenticated)
```http
POST /api/transcripts
Authorization: Basic <api-token>
Content-Type: application/json

{
  "ids": ["VIDEO_ID_1", "VIDEO_ID_2"]
}
```

### Rate Limits

- **Default**: 5 requests per 10 seconds
- **Extract**: 10 requests per minute
- **API**: 5 requests per 10 seconds

Rate limit exceeded returns `429 Too Many Requests` with `Retry-After` header.

For complete API documentation, visit `/api` page in the application.

---

## Architecture

### Agent-Based System

The application uses **multiple LangGraph agents**:

1. **Transcript Agent** - Fetches YouTube transcripts
2. **Summary Agent** - Generates AI summaries
3. **Podcast Agent** - Creates podcast conversations and audio

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed agent and architecture documentation.

### Technology Stack

- **Backend**: Flask (Python)
- **AI**: LangChain, OpenAI GPT
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth
- **Frontend**: HTML, CSS, JavaScript
- **Testing**: Pytest, Selenium

### Project Structure

```
Youtube_Podcast/
├── app.py                 # Main Flask application
├── config.py              # Configuration management
├── run.py                 # WSGI entry point
├── start.py               # Startup script with validation
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

---

## Database Setup

### Supabase Setup

1. **Create Supabase Project**
   - Go to https://supabase.com
   - Create a new project
   - Note your project URL and anon key

2. **Run Database Schema**
   - Open Supabase Dashboard > SQL Editor
   - Copy contents of `database_schema.sql`
   - Execute the SQL script

3. **Validate Schema**
   ```bash
   python scripts/validate_supabase_schema.py
   ```

### Database Tables

- **user_profiles** - User account information and plans
- **api_tokens** - API authentication tokens
- **usage_history** - User activity tracking

See [SUPABASE_SETUP.md](SUPABASE_SETUP.md) for detailed setup instructions.

---

## Deployment

### Production Deployment

1. **Set Environment Variables**
   ```bash
   export APP_ENV=production
   export SECRET_KEY=your_strong_secret
   export OPENAI_API_KEY=your_key
   export REACT_APP_SUPABASE_URL=your_url
   export REACT_APP_SUPABASE_ANON_KEY=your_key
   ```

2. **Install Production Server**
   ```bash
   pip install gunicorn
   ```

3. **Run with Gunicorn**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 run:app
   ```

4. **Setup Reverse Proxy (Nginx)**
   See [DEPLOYMENT.md](DEPLOYMENT.md) for Nginx configuration.

### Health Check

```bash
curl http://your-domain.com/healthz
```

Returns: `{"status": "ok", "service": "video-transcript-pro"}`

For complete deployment guide, see [DEPLOYMENT.md](DEPLOYMENT.md).

---

## Testing

### Run Automation Tests

```bash
# Start Flask app in one terminal
python start.py

# Run tests in another terminal
python run_tests.py
```

### Test Coverage

- Homepage loading
- User signup/login
- Transcript extraction
- Summary generation
- Podcast generation
- Navigation testing

Test reports are saved in `test_reports/` folder.

---

## Production Checklist

Before deploying to production, review [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md).

### Key Items

- [x] Rate limiting per user
- [x] Usage tracking
- [x] Database setup
- [ ] CSRF protection
- [ ] Input sanitization
- [ ] Monitoring setup
- [ ] SSL/TLS certificates

---

## Support

- **Documentation**: See files in `docs/` folder
- **API Docs**: Visit `/api` page in application
- **Support**: Visit `/support` page or email support@videotranscript.pro

---

## License

Copyright © 2025 VideoTranscript Pro. All rights reserved.
