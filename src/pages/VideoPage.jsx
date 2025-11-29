import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { supabase } from '../supabase';

export default function VideoPage({ videoId, onNavigate }) {
  const [transcript, setTranscript] = useState(null);
  const [segments, setSegments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('transcript');
  const [searchQuery, setSearchQuery] = useState('');
  const [currentTime, setCurrentTime] = useState(0);
  const { user } = useAuth();

  useEffect(() => {
    if (videoId) {
      loadTranscript();
    }
  }, [videoId]);

  const loadTranscript = async () => {
    try {
      const { data, error } = await supabase
        .from('transcripts')
        .select('*')
        .eq('video_id', videoId)
        .maybeSingle();

      if (error) throw error;

      if (data) {
        setTranscript(data);
        parseSegments(data.transcript_text);
      }
    } catch (error) {
      console.error('Error loading transcript:', error);
    } finally {
      setLoading(false);
    }
  };

  const parseSegments = (text) => {
    const words = text.split(' ');
    const segs = [];
    const wordsPerSegment = 15;

    for (let i = 0; i < words.length; i += wordsPerSegment) {
      const segmentWords = words.slice(i, i + wordsPerSegment);
      const startTime = (i / wordsPerSegment) * 10;

      segs.push({
        start: startTime,
        text: segmentWords.join(' '),
        index: i
      });
    }

    setSegments(segs);
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const jumpToTime = (time) => {
    setCurrentTime(time);
    const iframe = document.querySelector('iframe');
    if (iframe) {
      iframe.contentWindow.postMessage(JSON.stringify({
        event: 'command',
        func: 'seekTo',
        args: [time, true]
      }), '*');
    }
  };

  const copyTranscript = () => {
    if (transcript) {
      navigator.clipboard.writeText(transcript.transcript_text);
      alert('Transcript copied to clipboard!');
    }
  };

  const downloadTranscript = () => {
    if (!transcript) return;
    const blob = new Blob([transcript.transcript_text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `transcript-${videoId}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const filteredSegments = segments.filter(seg =>
    seg.text.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="video-page">
        <div className="loading-container">
          <span className="loading"></span>
          <p>Loading transcript...</p>
        </div>
      </div>
    );
  }

  if (!transcript) {
    return (
      <div className="video-page">
        <div className="empty-state">
          <h3>Transcript not found</h3>
          <button onClick={() => onNavigate('home')} className="btn btn-primary">
            Go Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="video-page">
      <div className="video-container">
        <div className="video-player">
          <iframe
            width="100%"
            height="100%"
            src={`https://www.youtube.com/embed/${videoId}?enablejsapi=1`}
            title="YouTube video player"
            frameBorder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          ></iframe>
        </div>

        <div className="video-info">
          <h1>{transcript.video_title}</h1>
          <div className="video-meta">
            <span className="meta-item">
              📅 {new Date(transcript.created_at).toLocaleDateString()}
            </span>
            <span className="meta-item">
              📝 {transcript.transcript_text.length} characters
            </span>
            <span className="meta-item">
              🌐 {transcript.language.toUpperCase()}
            </span>
          </div>
        </div>

        <div className="action-bar">
          <button onClick={copyTranscript} className="action-btn">
            <span className="icon">📋</span>
            <span>Copy</span>
          </button>
          <button onClick={downloadTranscript} className="action-btn">
            <span className="icon">💾</span>
            <span>Download</span>
          </button>
          <button onClick={() => onNavigate('home')} className="action-btn">
            <span className="icon">🔙</span>
            <span>Back</span>
          </button>
        </div>
      </div>

      <div className="transcript-panel">
        <div className="panel-header">
          <div className="tabs">
            <button
              className={`tab ${activeTab === 'transcript' ? 'active' : ''}`}
              onClick={() => setActiveTab('transcript')}
            >
              Transcript
            </button>
            <button
              className={`tab ${activeTab === 'summary' ? 'active' : ''}`}
              onClick={() => setActiveTab('summary')}
            >
              Summary
            </button>
            <button
              className={`tab ${activeTab === 'timestamps' ? 'active' : ''}`}
              onClick={() => setActiveTab('timestamps')}
            >
              Timestamps
            </button>
          </div>

          <div className="search-box">
            <input
              type="text"
              placeholder="Search in transcript..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="clear-search"
              >
                ✕
              </button>
            )}
          </div>
        </div>

        <div className="panel-content">
          {activeTab === 'transcript' && (
            <div className="transcript-view">
              {filteredSegments.length === 0 ? (
                <div className="no-results">No results found</div>
              ) : (
                filteredSegments.map((segment, index) => (
                  <div
                    key={index}
                    className={`transcript-segment ${
                      Math.floor(currentTime / 10) === Math.floor(segment.start / 10)
                        ? 'active'
                        : ''
                    }`}
                    onClick={() => jumpToTime(segment.start)}
                  >
                    <div className="segment-time">
                      {formatTime(segment.start)}
                    </div>
                    <div className="segment-text">
                      {searchQuery ? (
                        <span
                          dangerouslySetInnerHTML={{
                            __html: segment.text.replace(
                              new RegExp(searchQuery, 'gi'),
                              match => `<mark>${match}</mark>`
                            )
                          }}
                        />
                      ) : (
                        segment.text
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === 'summary' && (
            <div className="summary-view">
              <div className="summary-card">
                <h3>Quick Summary</h3>
                <p>
                  This video transcript contains {transcript.transcript_text.split(' ').length} words
                  and approximately {Math.ceil(transcript.transcript_text.length / 1000)} minutes of content.
                </p>
              </div>
              <div className="summary-card">
                <h3>Full Transcript</h3>
                <p className="summary-text">{transcript.transcript_text}</p>
              </div>
            </div>
          )}

          {activeTab === 'timestamps' && (
            <div className="timestamps-view">
              <div className="timestamps-header">
                <h3>Key Timestamps</h3>
                <p>Click any timestamp to jump to that part of the video</p>
              </div>
              {segments.map((segment, index) => (
                index % 5 === 0 && (
                  <div
                    key={index}
                    className="timestamp-item"
                    onClick={() => jumpToTime(segment.start)}
                  >
                    <div className="timestamp-time">
                      <span className="time-badge">{formatTime(segment.start)}</span>
                    </div>
                    <div className="timestamp-preview">
                      {segment.text.substring(0, 100)}...
                    </div>
                  </div>
                )
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
