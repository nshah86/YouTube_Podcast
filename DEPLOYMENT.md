# VideoTranscript Pro - Deployment Guide

## Pre-Deployment Checklist

### Required Configuration

- [x] Database schema applied to Supabase
- [x] Environment variables configured
- [x] SECRET_KEY generated
- [ ] OpenAI API key added to `.env`
- [x] All templates created
- [x] Requirements file ready

### Optional Configuration

- [ ] Stripe integration (deferred for later)
- [ ] Custom domain setup
- [ ] Email service integration

## Quick Deploy

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Edit `.env` and add your OpenAI API key:

```bash
OPENAI_API_KEY=sk-proj-your-actual-key
```

### 3. Start Application

```bash
# Development
python start.py

# Production
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 app:app
```

## Cloud Platform Deployment

### Railway

1. Connect GitHub repository
2. Add environment variables:
   - `SECRET_KEY`
   - `OPENAI_API_KEY`
   - `REACT_APP_SUPABASE_URL`
   - `REACT_APP_SUPABASE_ANON_KEY`
   - `APP_ENV=production`
3. Deploy automatically

### Render

1. Create new Web Service
2. Connect repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `gunicorn -w 4 -b 0.0.0.0:$PORT --timeout 120 app:app`
5. Add environment variables
6. Deploy

### Heroku

```bash
# Install Heroku CLI
heroku login
heroku create your-app-name

# Add buildpack
heroku buildpacks:set heroku/python

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set OPENAI_API_KEY=your-openai-key
heroku config:set APP_ENV=production

# Deploy
git push heroku main
```

## VPS Deployment

### Using Nginx + Gunicorn

1. **Install dependencies**
```bash
sudo apt update
sudo apt install python3-pip python3-venv nginx certbot
```

2. **Clone and setup**
```bash
git clone <repo-url>
cd Youtube_Podcast
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Create systemd service**
```bash
sudo nano /etc/systemd/system/videotranscript.service
```

```ini
[Unit]
Description=VideoTranscript Pro
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/Youtube_Podcast
Environment="PATH=/path/to/Youtube_Podcast/venv/bin"
ExecStart=/path/to/Youtube_Podcast/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 --timeout 120 app:app

[Install]
WantedBy=multi-user.target
```

4. **Configure Nginx**
```bash
sudo nano /etc/nginx/sites-available/videotranscript
```

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

5. **Enable and start**
```bash
sudo ln -s /etc/nginx/sites-available/videotranscript /etc/nginx/sites-enabled/
sudo systemctl enable videotranscript
sudo systemctl start videotranscript
sudo systemctl reload nginx
```

6. **Setup SSL**
```bash
sudo certbot --nginx -d yourdomain.com
```

## Database

Database is already configured in Supabase with:
- Core tables created
- RLS policies enabled
- Indexes optimized
- Migrations applied

## Monitoring

### Health Check Endpoint

```bash
curl https://yourdomain.com/healthz
```

### Logs

```bash
# Development
Check console output

# Production (systemd)
sudo journalctl -u videotranscript -f

# Production (cloud)
Check platform dashboard
```

## Troubleshooting

### Application won't start
- Check Python version (3.8+)
- Verify all dependencies installed
- Check environment variables
- Review error logs

### Database errors
- Verify Supabase credentials
- Check internet connection
- Confirm migrations applied

### OpenAI errors
- Verify API key is correct
- Check API credit balance
- Review rate limits

## Security Notes

- Always use HTTPS in production
- Keep SECRET_KEY secure and random
- Never commit `.env` to version control
- Enable RLS on all database tables (already done)
- Monitor for suspicious activity
- Keep dependencies updated

## Next Steps

1. Test all features locally
2. Deploy to staging environment
3. Perform full testing
4. Deploy to production
5. Monitor application health
6. Set up backups and monitoring

---

**Current Status**: Ready for deployment
**Last Updated**: 2025-11-29
