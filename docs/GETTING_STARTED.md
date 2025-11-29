# Getting Started Guide

## For New Users

### Step 1: Install Dependencies

```bash
# Create virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### Step 2: Configure API Keys

Create a `.env` file:

```env
OPENAI_API_KEY=sk-...
SECRET_KEY=generate-a-random-secret-key
REACT_APP_SUPABASE_URL=https://your-project.supabase.co
REACT_APP_SUPABASE_ANON_KEY=your-anon-key
```

### Step 3: Setup Database (Optional for Authentication)

1. Go to Supabase Dashboard
2. Run `database_schema.sql` in SQL Editor
3. Validate: `python scripts/validate_supabase_schema.py`

### Step 4: Start the Application

```bash
python start.py
```

Visit `http://127.0.0.1:5000`

## For Developers

### Project Structure

- `app.py` - Main Flask application
- `src/youtube_podcast/agents/` - LangGraph agents
- `templates/` - HTML templates
- `static/` - CSS and JavaScript
- `tests/` - Test suite

### Running Tests

```bash
# Start app
python start.py

# In another terminal
python run_tests.py
```

### Development Workflow

1. Make changes to code
2. Run tests: `python run_tests.py`
3. Check linting: `python -m flake8 app.py`
4. Test manually in browser

## For Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete production deployment guide.

Key steps:
1. Set `APP_ENV=production`
2. Configure all environment variables
3. Run database schema
4. Use Gunicorn/uWSGI
5. Setup Nginx reverse proxy
6. Configure SSL/TLS

