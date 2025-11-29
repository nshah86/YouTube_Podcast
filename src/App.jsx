import { useState } from 'react';

function App() {
  const [videoUrl, setVideoUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [transcript, setTranscript] = useState(null);
  const [error, setError] = useState(null);

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
    setLoading(true);
    setError(null);
    setTranscript(null);

    try {
      const videoId = extractVideoId(videoUrl);

      if (!videoId) {
        throw new Error('Invalid YouTube URL. Please enter a valid YouTube video URL.');
      }

      // Using youtube-transcript-api via a CORS proxy
      const proxyUrl = 'https://corsproxy.io/?';
      const apiUrl = `${proxyUrl}https://youtube-transcript-api.vercel.app/api/transcript?videoId=${videoId}`;

      const response = await fetch(apiUrl);

      if (!response.ok) {
        throw new Error('Failed to fetch transcript. Make sure the video has captions enabled.');
      }

      const data = await response.json();

      if (!data || !data.transcript || data.transcript.length === 0) {
        throw new Error('No transcript available for this video. Please try a different video with captions.');
      }

      // Combine transcript segments
      const fullTranscript = data.transcript
        .map(item => item.text)
        .join(' ')
        .replace(/\s+/g, ' ')
        .trim();

      setTranscript({
        videoId,
        text: fullTranscript,
        videoTitle: data.title || 'YouTube Video',
        segments: data.transcript.length,
        length: fullTranscript.length
      });

    } catch (err) {
      setError(err.message || 'An error occurred while fetching the transcript.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (videoUrl.trim()) {
      fetchTranscript();
    }
  };

  const downloadTranscript = () => {
    if (!transcript) return;

    const blob = new Blob([transcript.text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `transcript-${transcript.videoId}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const copyToClipboard = () => {
    if (!transcript) return;
    navigator.clipboard.writeText(transcript.text);
    alert('Transcript copied to clipboard!');
  };

  return (
    <div className="container">
      <nav className="nav">
        <div className="nav-brand">VideoTranscript Pro</div>
        <div className="nav-links">
          <a href="#" className="nav-link">Home</a>
          <a href="#features" className="nav-link">Features</a>
          <a href="#" className="nav-link">API</a>
        </div>
      </nav>

      <div className="hero">
        <h1>Extract YouTube Transcripts Instantly</h1>
        <p>Get accurate transcripts from any YouTube video in seconds</p>
      </div>

      <div className="card">
        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <input
              type="text"
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
              placeholder="Paste YouTube URL here... (e.g., https://youtube.com/watch?v=...)"
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
                <h3>{transcript.videoTitle}</h3>
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
            <div className="transcript-content">
              {transcript.text}
            </div>
          </div>
        )}
      </div>

      <div id="features" className="features">
        <div className="feature-card">
          <h3>⚡ Instant Extraction</h3>
          <p>Get transcripts from any YouTube video in seconds. Just paste the URL and click extract.</p>
        </div>
        <div className="feature-card">
          <h3>📝 Accurate Text</h3>
          <p>Receive clean, formatted transcripts with proper punctuation and spacing.</p>
        </div>
        <div className="feature-card">
          <h3>💾 Easy Export</h3>
          <p>Download transcripts as text files or copy directly to your clipboard.</p>
        </div>
        <div className="feature-card">
          <h3>🎯 No Limits</h3>
          <p>Extract transcripts from unlimited videos, completely free to use.</p>
        </div>
      </div>

      <div className="stats">
        <div className="stat-card">
          <h4>100%</h4>
          <p>Free Forever</p>
        </div>
        <div className="stat-card">
          <h4>0s</h4>
          <p>Processing Time</p>
        </div>
        <div className="stat-card">
          <h4>∞</h4>
          <p>Unlimited Videos</p>
        </div>
      </div>
    </div>
  );
}

export default App;
