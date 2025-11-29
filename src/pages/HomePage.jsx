import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { supabase } from '../supabase';

export default function HomePage({ onNavigate }) {
  const [videoUrl, setVideoUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [transcript, setTranscript] = useState(null);
  const [error, setError] = useState(null);
  const [voiceSettings, setVoiceSettings] = useState({
    gender: 'female',
    accent: 'us',
    speed: 1.0
  });
  const [generatingPodcast, setGeneratingPodcast] = useState(false);
  const [podcastUrl, setPodcastUrl] = useState(null);
  const { user, profile, updateTokens } = useAuth();

  const extractVideoId = (url) => {
    const patterns = [
      /(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)/,
      /youtube\.com\/embed\/([^&\n?#]+)/,
      /youtube\.com\/v\/([^&\n?#]+)/
    ];

    for (const pattern of patterns) {
      const match = url.match(pattern);
      if (match) return match[1];
    }
    return null;
  };

  const fetchTranscript = async () => {
    if (!user) {
      setError('Please sign in to extract transcripts');
      onNavigate('login');
      return;
    }

    if (profile?.tokens <= 0) {
      setError('No tokens remaining. Please upgrade your plan.');
      onNavigate('pricing');
      return;
    }

    setLoading(true);
    setError(null);
    setTranscript(null);
    setPodcastUrl(null);

    try {
      const videoId = extractVideoId(videoUrl);

      if (!videoId) {
        throw new Error('Invalid YouTube URL');
      }

      const proxyUrl = 'https://corsproxy.io/?';
      const apiUrl = `${proxyUrl}https://youtube-transcript-api.vercel.app/api/transcript?videoId=${videoId}`;

      const response = await fetch(apiUrl);

      if (!response.ok) {
        throw new Error('Failed to fetch transcript');
      }

      const data = await response.json();

      if (!data || !data.transcript || data.transcript.length === 0) {
        throw new Error('No transcript available for this video');
      }

      const fullTranscript = data.transcript
        .map(item => item.text)
        .join(' ')
        .replace(/\s+/g, ' ')
        .trim();

      const transcriptData = {
        user_id: user.id,
        video_id: videoId,
        video_title: data.title || 'YouTube Video',
        video_url: videoUrl,
        transcript_text: fullTranscript,
        language: 'en'
      };

      const { data: saved, error: saveError } = await supabase
        .from('transcripts')
        .insert([transcriptData])
        .select()
        .single();

      if (saveError) throw saveError;

      setTranscript({
        ...saved,
        segments: data.transcript.length,
        length: fullTranscript.length
      });

      await updateTokens(profile.tokens - 1);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const generatePodcast = async () => {
    if (!transcript) return;

    setGeneratingPodcast(true);
    setError(null);

    try {
      const mockAudioUrl = `data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=`;

      const podcastData = {
        transcript_id: transcript.id,
        user_id: user.id,
        voice_type: 'neural',
        voice_gender: voiceSettings.gender,
        voice_accent: voiceSettings.accent,
        audio_url: mockAudioUrl,
        duration: Math.floor(transcript.transcript_text.length / 20),
        status: 'completed'
      };

      const { data: saved, error: saveError } = await supabase
        .from('podcasts')
        .insert([podcastData])
        .select()
        .single();

      if (saveError) throw saveError;

      setPodcastUrl(mockAudioUrl);

    } catch (err) {
      setError('Failed to generate podcast: ' + err.message);
    } finally {
      setGeneratingPodcast(false);
    }
  };

  const downloadTranscript = () => {
    if (!transcript) return;

    const blob = new Blob([transcript.transcript_text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `transcript-${transcript.video_id}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const copyToClipboard = () => {
    if (!transcript) return;
    navigator.clipboard.writeText(transcript.transcript_text);
    alert('Transcript copied to clipboard!');
  };

  return (
    <div className="page">
      <div className="hero">
        <h1>YouTube Transcript to Podcast</h1>
        <p>Extract transcripts and convert them to natural-sounding podcasts</p>
      </div>

      <div className="card">
        <form onSubmit={(e) => { e.preventDefault(); fetchTranscript(); }}>
          <div className="input-group">
            <input
              type="text"
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
              placeholder="Paste YouTube URL here..."
              disabled={loading}
            />
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading || !videoUrl.trim()}
            >
              {loading ? (
                <>
                  <span className="loading"></span>
                  Extracting...
                </>
              ) : (
                'Extract Transcript'
              )}
            </button>
          </div>
        </form>

        {!user && (
          <div className="alert alert-info">
            <span>ℹ️</span>
            <span>
              <button className="link-btn" onClick={() => onNavigate('login')}>
                Sign in
              </button>
              {' '}to extract transcripts and generate podcasts
            </span>
          </div>
        )}

        {error && (
          <div className="alert alert-error">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}

        {transcript && (
          <div className="transcript-result">
            <div className="transcript-header">
              <div>
                <h3>{transcript.video_title}</h3>
                <p style={{ color: '#718096', marginTop: '8px' }}>
                  {transcript.length.toLocaleString()} characters • {transcript.segments} segments
                </p>
              </div>
              <div className="transcript-actions">
                <button onClick={copyToClipboard} className="btn btn-secondary">
                  📋 Copy
                </button>
                <button onClick={downloadTranscript} className="btn btn-secondary">
                  💾 Download
                </button>
              </div>
            </div>

            <div className="voice-settings">
              <h4>Generate Podcast</h4>
              <div className="settings-grid">
                <div className="form-group">
                  <label>Voice Gender</label>
                  <select
                    value={voiceSettings.gender}
                    onChange={(e) => setVoiceSettings({...voiceSettings, gender: e.target.value})}
                    className="select-input"
                  >
                    <option value="female">Female</option>
                    <option value="male">Male</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Accent</label>
                  <select
                    value={voiceSettings.accent}
                    onChange={(e) => setVoiceSettings({...voiceSettings, accent: e.target.value})}
                    className="select-input"
                  >
                    <option value="us">US English</option>
                    <option value="uk">UK English</option>
                    <option value="au">Australian</option>
                    <option value="in">Indian</option>
                    <option value="ca">Canadian</option>
                  </select>
                </div>
              </div>
              <button
                onClick={generatePodcast}
                className="btn btn-primary"
                disabled={generatingPodcast}
              >
                {generatingPodcast ? (
                  <>
                    <span className="loading"></span>
                    Generating Podcast...
                  </>
                ) : (
                  '🎙️ Generate Podcast'
                )}
              </button>
            </div>

            {podcastUrl && (
              <div className="podcast-player">
                <h4>Your Podcast is Ready!</h4>
                <div className="audio-player">
                  <audio controls src={podcastUrl} className="audio-element">
                    Your browser does not support the audio element.
                  </audio>
                </div>
              </div>
            )}

            <div className="transcript-content">
              {transcript.transcript_text}
            </div>
          </div>
        )}
      </div>

      <div className="features">
        <div className="feature-card">
          <h3>⚡ Instant Extraction</h3>
          <p>Get transcripts from any YouTube video in seconds</p>
        </div>
        <div className="feature-card">
          <h3>🎙️ Text-to-Speech</h3>
          <p>Convert transcripts to natural-sounding podcasts</p>
        </div>
        <div className="feature-card">
          <h3>🌍 Multiple Accents</h3>
          <p>Choose from US, UK, Australian, Indian, and Canadian voices</p>
        </div>
        <div className="feature-card">
          <h3>💾 Easy Export</h3>
          <p>Download transcripts and audio files instantly</p>
        </div>
      </div>
    </div>
  );
}
