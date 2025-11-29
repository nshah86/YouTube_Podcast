# Deployment Guide

## Pre-Deployment Checklist

### 1. Environment Setup

Create `.env` file with required variables:

```env
# Flask
SECRET_KEY=your-secret-key-here
FLASK_ENV=production

# Supabase
REACT_APP_SUPABASE_URL=https://your-project.supabase.co
REACT_APP_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# OpenAI
OPENAI_API_KEY=your-openai-key

# Optional
LOG_LEVEL=INFO
```

### 2. Database Setup

1. **Create Supabase Project**
   - Go to https://supabase.com
   - Create new project
   - Note your project URL and anon key

2. **Run Database Schema**
   - Open Supabase Dashboard > SQL Editor
   - Copy contents of `database_schema.sql`
   - Execute the SQL script
   - Verify tables are created

3. **Validate Schema**
   ```bash
   python scripts/validate_supabase_schema.py
   ```

### 3. Test Suite

Run full test suite before deployment:

```bash
# Start Flask app in one terminal
python start.py

# Run tests in another terminal
python run_tests.py
```

### 4. Production Server Setup

#### Using Gunicorn (Recommended)

```bash
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 run:app
```

#### Using uWSGI

```bash
pip install uwsgi

# Run with uWSGI
uwsgi --http :8000 --wsgi-file run.py --callable app
```

### 5. Reverse Proxy (Nginx)

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/your/app/static;
        expires 30d;
    }
}
```

### 6. SSL/TLS Setup

Use Let's Encrypt for free SSL:

```bash
sudo certbot --nginx -d yourdomain.com
```

### 7. Monitoring

Set up monitoring:
- **Sentry** for error tracking
- **DataDog** or **New Relic** for performance
- **Uptime monitoring** (UptimeRobot, Pingdom)

### 8. Backup Strategy

- **Database**: Supabase automatic backups (verify retention policy)
- **Files**: Backup `output/` directory regularly
- **Configuration**: Version control all config files

## Post-Deployment

1. Verify health endpoint: `https://yourdomain.com/healthz`
2. Test user signup/login
3. Test transcript extraction
4. Monitor error logs
5. Check performance metrics

## Rollback Plan

1. Keep previous version in separate directory
2. Database migrations should be reversible
3. Test rollback procedure before deployment

## Maintenance

- Monitor token usage
- Review error logs daily
- Update dependencies monthly
- Run test suite after updates
- Backup database weekly

