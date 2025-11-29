import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { supabase } from '../supabase';

export default function PodcastsPage() {
  const [podcasts, setPodcasts] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      loadPodcasts();
    }
  }, [user]);

  const loadPodcasts = async () => {
    try {
      const { data, error } = await supabase
        .from('podcasts')
        .select(`
          *,
          transcripts (
            video_title,
            video_url
          )
        `)
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });

      if (error) throw error;
      setPodcasts(data || []);
    } catch (error) {
      console.error('Error loading podcasts:', error);
    } finally {
      setLoading(false);
    }
  };

  const deletePodcast = async (id) => {
    if (!confirm('Are you sure you want to delete this podcast?')) return;

    try {
      const { error } = await supabase
        .from('podcasts')
        .delete()
        .eq('id', id);

      if (error) throw error;
      setPodcasts(podcasts.filter(p => p.id !== id));
    } catch (error) {
      console.error('Error deleting podcast:', error);
      alert('Failed to delete podcast');
    }
  };

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <div className="page">
        <div className="loading-container">
          <span className="loading"></span>
          <p>Loading your podcasts...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Your Podcasts</h1>
        <p>Listen to your generated podcasts</p>
      </div>

      {podcasts.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">🎙️</div>
          <h3>No podcasts yet</h3>
          <p>Generate your first podcast from a transcript</p>
        </div>
      ) : (
        <div className="podcast-grid">
          {podcasts.map((podcast) => (
            <div key={podcast.id} className="podcast-card">
              <div className="podcast-card-header">
                <div className="podcast-icon">🎙️</div>
                <div className="podcast-info">
                  <h3>{podcast.transcripts?.video_title || 'Untitled'}</h3>
                  <div className="podcast-meta">
                    <span className="podcast-badge">
                      {podcast.voice_gender} • {podcast.voice_accent.toUpperCase()}
                    </span>
                    <span>{formatDuration(podcast.duration)}</span>
                  </div>
                </div>
                <button
                  onClick={() => deletePodcast(podcast.id)}
                  className="icon-btn"
                  title="Delete"
                >
                  🗑️
                </button>
              </div>

              {podcast.status === 'completed' && podcast.audio_url && (
                <div className="podcast-player">
                  <audio controls src={podcast.audio_url} className="audio-element">
                    Your browser does not support the audio element.
                  </audio>
                </div>
              )}

              {podcast.status === 'processing' && (
                <div className="podcast-status">
                  <span className="loading"></span>
                  <span>Processing podcast...</span>
                </div>
              )}

              <div className="podcast-card-footer">
                <span>📅 {new Date(podcast.created_at).toLocaleDateString()}</span>
                {podcast.transcripts?.video_url && (
                  <a
                    href={podcast.transcripts.video_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="podcast-link"
                  >
                    View Source →
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
