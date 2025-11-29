# VideoTranscript Pro

Transform YouTube videos into transcripts, AI summaries, and conversational podcasts.

## Features

- **Extract Transcripts**: Get accurate transcripts from any YouTube video instantly
- **AI Summaries**: Generate intelligent summaries powered by OpenAI
- **Create Podcasts**: Convert videos into engaging conversational podcasts
- **Bulk Processing**: Process multiple videos or entire playlists at once
- **API Access**: REST API for programmatic access
- **User Authentication**: Secure user accounts with Supabase
- **Usage Tracking**: Monitor and manage your usage limits

## Quick Start

### Prerequisites

- Python 3.8 or higher
- OpenAI API key (for AI features)
- Supabase account (database is pre-configured)

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd Youtube_Podcast
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**

Edit `.env` file and add your OpenAI API key:
```bash
OPENAI_API_KEY=sk-proj-your-actual-openai-key
```

The Supabase database is already configured and ready to use.

4. **Start the application**
```bash
python start.py
```

5. **Open your browser**
```
http://localhost:5000
```

## Project Structure

```
Youtube_Podcast/
├── app.py                      # Main Flask application
├── config.py                   # Configuration management
├── start.py                    # Application entry point
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
├── .gitignore                  # Git ignore rules
├── src/
│   └── youtube_podcast/
│       ├── agents/            # AI agents for processing
│       │   ├── summary_agent.py
│       │   ├── podcast_agent.py
│       │   └── transcript_agent.py
│       ├── config/            # Configuration settings
│       │   └── settings.py
│       ├── models/            # Data models
│       │   └── state.py
│       └── utils/             # Utility modules
│           ├── auth.py        # Authentication
│           ├── supabase_client.py
│           ├── youtube_utils.py
│           ├── bulk_extract.py
│           ├── usage_tracker.py
│           └── rate_limiter.py
├── static/
│   ├── css/                   # Stylesheets
│   └── js/                    # JavaScript files
├── templates/                 # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── about.html
│   ├── features.html
│   ├── pricing.html
│   ├── api.html
│   ├── support.html
│   ├── 404.html
│   └── 500.html
└── supabase/
    └── migrations/            # Database migrations
```

## Configuration

### Environment Variables

Required variables in `.env`:

```bash
# Flask
SECRET_KEY=<secure-random-key>
FLASK_ENV=development
APP_ENV=development

# OpenAI (required for AI features)
OPENAI_API_KEY=sk-proj-your-key

# Supabase (pre-configured)
REACT_APP_SUPABASE_URL=<your-supabase-url>
REACT_APP_SUPABASE_ANON_KEY=<your-anon-key>

# Optional
OUTPUT_DIR=./output
LOG_LEVEL=INFO
```

## Database

The Supabase database is pre-configured with:

- **user_profiles**: User account management
- **api_tokens**: API authentication
- **usage_history**: Usage tracking
- **subscriptions**: Subscription management
- **payments**: Payment records
- **api_usage**: API usage analytics

All tables have Row Level Security (RLS) enabled for data protection.

## Usage

### Extract Transcript

1. Go to the home page
2. Paste a YouTube URL
3. Click "Extract Transcript"
4. Download or process further

### Generate Summary

After extracting a transcript:
1. Click "Generate Summary"
2. AI will create a concise summary
3. Download or view the summary

### Create Podcast

After extracting a transcript:
1. Click "Create Podcast"
2. AI will generate a conversational podcast
3. Download the MP3 file

### API Access

Generate an API token from your account page, then use:

```bash
curl -X POST https://your-domain.com/api/v1/extract \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://youtube.com/watch?v=..."}'
```

## Plans & Limits

- **Free**: 25 transcripts/month
- **Plus**: 1,000 transcripts/month + API access
- **Pro**: 3,000 transcripts/month + advanced features
- **Enterprise**: Custom limits + dedicated support

## Production Deployment

### Option 1: Traditional Server (VPS)

```bash
# Install dependencies
pip install -r requirements.txt gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 app:app

# Set up Nginx reverse proxy
# Configure SSL with Let's Encrypt
```

### Option 2: Cloud Platform

Deploy to Railway, Render, Heroku, or similar:

1. Connect GitHub repository
2. Set environment variables in dashboard
3. Platform will auto-deploy

### Production Checklist

- [ ] Set `APP_ENV=production`
- [ ] Configure strong `SECRET_KEY`
- [ ] Enable HTTPS/SSL
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Review security settings

## Development

### Running Tests

```bash
pip install pytest pytest-flask
pytest
```

### Code Structure

- Follow Flask best practices
- Use type hints where possible
- Keep routes focused and simple
- Separate business logic from routes

## Security

- All sensitive data protected by RLS policies
- CSRF protection enabled
- Secure session management
- Rate limiting on API endpoints
- Input validation on all forms

## Troubleshooting

### Application won't start

Check that:
- Python 3.8+ is installed
- All dependencies are installed
- `.env` file exists
- Supabase credentials are correct

### AI features not working

Verify:
- `OPENAI_API_KEY` is set correctly
- API key has sufficient credits
- Check error logs for details

### Database connection issues

Ensure:
- Supabase URL and keys are correct
- Internet connection is active
- Supabase project is active

## Support

- **Email**: support@videotranscriptpro.com
- **Documentation**: See `/docs` folder (coming soon)
- **Issues**: Open an issue on GitHub

## License

Copyright © 2025 VideoTranscript Pro. All rights reserved.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Changelog

### v1.0.0 (2025-11-29)
- Initial release
- YouTube transcript extraction
- AI-powered summaries
- Podcast generation
- User authentication
- API access
- Usage tracking
- Bulk processing

## Roadmap

- [ ] Multi-language support
- [ ] Video analysis features
- [ ] Advanced podcast customization
- [ ] Team collaboration features
- [ ] Chrome extension
- [ ] Mobile app

---

Built with Flask, OpenAI, and Supabase.
