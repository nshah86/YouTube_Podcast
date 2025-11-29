# Supabase Setup Guide for VideoTranscript Pro

## Step 1: Create Supabase Project

1. Go to https://supabase.com
2. Sign up or log in
3. Create a new project
4. Note your project URL and anon key

## Step 2: Configure Environment Variables

Add to your `.env` file:

```env
REACT_APP_SUPABASE_URL=https://your-project.supabase.co
REACT_APP_SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-key-here  # Optional, for admin operations
```

## Step 3: Run Database Schema

1. Open your Supabase project dashboard
2. Go to SQL Editor
3. Copy and paste the contents of `database_schema.sql`
4. Click "Run" to execute

This will create:
- `user_profiles` table
- `api_tokens` table
- `usage_history` table
- Row Level Security (RLS) policies
- Automatic user profile creation trigger

## Step 4: Configure OAuth Providers (Optional)

### Google OAuth
1. Go to Authentication > Providers in Supabase dashboard
2. Enable Google provider
3. Add your Google OAuth credentials

### Microsoft OAuth
1. Go to Authentication > Providers in Supabase dashboard
2. Enable Azure provider
3. Add your Microsoft OAuth credentials

## Step 5: Test the Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the app:
```bash
python start.py
```

3. Visit http://127.0.0.1:5000/login
4. Try creating an account

## Database Tables

### user_profiles
- `id` (UUID) - References auth.users
- `email` (TEXT) - User email
- `plan` (TEXT) - free, plus, pro, enterprise
- `tokens_used` (INTEGER) - Current month usage
- `tokens_limit` (INTEGER) - Monthly limit
- `created_at`, `updated_at` (TIMESTAMP)

### api_tokens
- `id` (UUID) - Primary key
- `user_id` (UUID) - References user_profiles
- `token` (TEXT) - API token string
- `name` (TEXT) - Token name/description
- `last_used_at` (TIMESTAMP)
- `created_at` (TIMESTAMP)

### usage_history
- `id` (UUID) - Primary key
- `user_id` (UUID) - References user_profiles
- `video_id` (TEXT) - YouTube video ID
- `video_url` (TEXT) - Full YouTube URL
- `transcript_length` (INTEGER)
- `operation_type` (TEXT) - extract, summary, podcast
- `tokens_used` (INTEGER)
- `created_at` (TIMESTAMP)

## Security

- Row Level Security (RLS) is enabled on all tables
- Users can only access their own data
- API tokens are scoped to users
- All authentication handled by Supabase Auth

