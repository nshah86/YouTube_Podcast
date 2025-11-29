import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { supabase } from '../supabase';

export default function ApiPage() {
  const { user } = useAuth();
  const [apiKey, setApiKey] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (user) {
      const key = `yt_${user.id.substring(0, 8)}_${Math.random().toString(36).substring(2, 15)}`;
      setApiKey(key);
    }
  }, [user]);

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const codeExamples = {
    curl: `curl -X POST https://nshah86-youtube-podc-2bw8.bolt.host/api/transcript \\
  -H "Authorization: Bearer ${apiKey || 'YOUR_API_KEY'}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "video_url": "https://youtube.com/watch?v=dQw4w9WgXcQ"
  }'`,

    javascript: `const response = await fetch('https://nshah86-youtube-podc-2bw8.bolt.host/api/transcript', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ${apiKey || 'YOUR_API_KEY'}',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    video_url: 'https://youtube.com/watch?v=dQw4w9WgXcQ'
  })
});

const data = await response.json();
console.log(data.transcript);`,

    python: `import requests

url = 'https://nshah86-youtube-podc-2bw8.bolt.host/api/transcript'
headers = {
    'Authorization': 'Bearer ${apiKey || 'YOUR_API_KEY'}',
    'Content-Type': 'application/json'
}
data = {
    'video_url': 'https://youtube.com/watch?v=dQw4w9WgXcQ'
}

response = requests.post(url, headers=headers, json=data)
transcript = response.json()
print(transcript['transcript'])`
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1>API Documentation</h1>
        <p>Integrate YouTube transcript extraction into your applications</p>
      </div>

      {!user && (
        <div className="alert alert-info">
          <span>ℹ️</span>
          <span>Sign in to get your API key and start using the API</span>
        </div>
      )}

      {user && (
        <div className="card">
          <h3>Your API Key</h3>
          <div className="api-key-section">
            <code className="api-key">{apiKey}</code>
            <button
              onClick={() => copyToClipboard(apiKey)}
              className="btn btn-secondary"
            >
              {copied ? '✓ Copied!' : '📋 Copy'}
            </button>
          </div>
          <p className="api-warning">
            ⚠️ Keep your API key secret. Do not share it publicly or commit it to version control.
          </p>
        </div>
      )}

      <div className="card">
        <h3>Endpoints</h3>

        <div className="endpoint-section">
          <div className="endpoint-header">
            <span className="http-method post">POST</span>
            <code>/api/transcript</code>
          </div>
          <p>Extract transcript from a YouTube video</p>

          <h4>Request Body</h4>
          <pre className="code-block">{`{
  "video_url": "https://youtube.com/watch?v=VIDEO_ID"
}`}</pre>

          <h4>Response</h4>
          <pre className="code-block">{`{
  "success": true,
  "data": {
    "video_id": "VIDEO_ID",
    "video_title": "Video Title",
    "transcript": "Full transcript text...",
    "language": "en",
    "duration": 120
  }
}`}</pre>
        </div>

        <div className="endpoint-section">
          <div className="endpoint-header">
            <span className="http-method post">POST</span>
            <code>/api/generate-podcast</code>
          </div>
          <p>Generate podcast from transcript</p>

          <h4>Request Body</h4>
          <pre className="code-block">{`{
  "transcript_id": "uuid",
  "voice_gender": "female",
  "voice_accent": "us"
}`}</pre>

          <h4>Response</h4>
          <pre className="code-block">{`{
  "success": true,
  "data": {
    "podcast_id": "uuid",
    "audio_url": "https://...",
    "duration": 180,
    "status": "completed"
  }
}`}</pre>
        </div>
      </div>

      <div className="card">
        <h3>Code Examples</h3>

        <div className="code-example">
          <h4>cURL</h4>
          <div className="code-block-container">
            <pre className="code-block">{codeExamples.curl}</pre>
            <button
              onClick={() => copyToClipboard(codeExamples.curl)}
              className="copy-btn"
            >
              📋
            </button>
          </div>
        </div>

        <div className="code-example">
          <h4>JavaScript</h4>
          <div className="code-block-container">
            <pre className="code-block">{codeExamples.javascript}</pre>
            <button
              onClick={() => copyToClipboard(codeExamples.javascript)}
              className="copy-btn"
            >
              📋
            </button>
          </div>
        </div>

        <div className="code-example">
          <h4>Python</h4>
          <div className="code-block-container">
            <pre className="code-block">{codeExamples.python}</pre>
            <button
              onClick={() => copyToClipboard(codeExamples.python)}
              className="copy-btn"
            >
              📋
            </button>
          </div>
        </div>
      </div>

      <div className="card">
        <h3>Rate Limits</h3>
        <div className="rate-limit-grid">
          <div className="rate-limit-item">
            <div className="rate-limit-value">25</div>
            <div className="rate-limit-label">requests/month (Free)</div>
          </div>
          <div className="rate-limit-item">
            <div className="rate-limit-value">1000</div>
            <div className="rate-limit-label">requests/month (Plus)</div>
          </div>
          <div className="rate-limit-item">
            <div className="rate-limit-value">3000</div>
            <div className="rate-limit-label">requests/month (Pro)</div>
          </div>
        </div>
      </div>
    </div>
  );
}
