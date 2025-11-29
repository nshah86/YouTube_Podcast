/*
  # Create YouTube Transcript to Podcast Schema

  1. New Tables
    - `profiles`
      - `id` (uuid, references auth.users, primary key)
      - `email` (text)
      - `tokens` (integer, default 25)
      - `plan` (text, default 'free')
      - `created_at` (timestamptz)
      
    - `transcripts`
      - `id` (uuid, primary key)
      - `user_id` (uuid, references profiles)
      - `video_id` (text)
      - `video_title` (text)
      - `video_url` (text)
      - `transcript_text` (text)
      - `language` (text, default 'en')
      - `created_at` (timestamptz)
      
    - `podcasts`
      - `id` (uuid, primary key)
      - `transcript_id` (uuid, references transcripts)
      - `user_id` (uuid, references profiles)
      - `voice_type` (text)
      - `voice_gender` (text)
      - `voice_accent` (text)
      - `audio_url` (text)
      - `duration` (integer)
      - `status` (text, default 'processing')
      - `created_at` (timestamptz)

  2. Security
    - Enable RLS on all tables
    - Add policies for authenticated users to access their own data
*/

-- Create profiles table
CREATE TABLE IF NOT EXISTS profiles (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email text NOT NULL,
  tokens integer DEFAULT 25,
  plan text DEFAULT 'free',
  created_at timestamptz DEFAULT now()
);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile"
  ON profiles FOR SELECT
  TO authenticated
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON profiles FOR UPDATE
  TO authenticated
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

-- Create transcripts table
CREATE TABLE IF NOT EXISTS transcripts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES profiles(id) ON DELETE CASCADE,
  video_id text NOT NULL,
  video_title text DEFAULT '',
  video_url text NOT NULL,
  transcript_text text NOT NULL,
  language text DEFAULT 'en',
  created_at timestamptz DEFAULT now()
);

ALTER TABLE transcripts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own transcripts"
  ON transcripts FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own transcripts"
  ON transcripts FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own transcripts"
  ON transcripts FOR DELETE
  TO authenticated
  USING (auth.uid() = user_id);

-- Create podcasts table
CREATE TABLE IF NOT EXISTS podcasts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  transcript_id uuid REFERENCES transcripts(id) ON DELETE CASCADE,
  user_id uuid REFERENCES profiles(id) ON DELETE CASCADE,
  voice_type text DEFAULT 'neural',
  voice_gender text DEFAULT 'female',
  voice_accent text DEFAULT 'us',
  audio_url text DEFAULT '',
  duration integer DEFAULT 0,
  status text DEFAULT 'processing',
  created_at timestamptz DEFAULT now()
);

ALTER TABLE podcasts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own podcasts"
  ON podcasts FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own podcasts"
  ON podcasts FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own podcasts"
  ON podcasts FOR UPDATE
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own podcasts"
  ON podcasts FOR DELETE
  TO authenticated
  USING (auth.uid() = user_id);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_transcripts_user_id ON transcripts(user_id);
CREATE INDEX IF NOT EXISTS idx_transcripts_video_id ON transcripts(video_id);
CREATE INDEX IF NOT EXISTS idx_podcasts_user_id ON podcasts(user_id);
CREATE INDEX IF NOT EXISTS idx_podcasts_transcript_id ON podcasts(transcript_id);
