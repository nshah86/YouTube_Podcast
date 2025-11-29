import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { supabase } from '../supabase';

export default function HistoryPage() {
  const [transcripts, setTranscripts] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      loadTranscripts();
    }
  }, [user]);

  const loadTranscripts = async () => {
    try {
      const { data, error } = await supabase
        .from('transcripts')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });

      if (error) throw error;
      setTranscripts(data || []);
    } catch (error) {
      console.error('Error loading transcripts:', error);
    } finally {
      setLoading(false);
    }
  };

  const deleteTranscript = async (id) => {
    if (!confirm('Are you sure you want to delete this transcript?')) return;

    try {
      const { error } = await supabase
        .from('transcripts')
        .delete()
        .eq('id', id);

      if (error) throw error;
      setTranscripts(transcripts.filter(t => t.id !== id));
    } catch (error) {
      console.error('Error deleting transcript:', error);
      alert('Failed to delete transcript');
    }
  };

  const downloadTranscript = (transcript) => {
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

  if (loading) {
    return (
      <div className="page">
        <div className="loading-container">
          <span className="loading"></span>
          <p>Loading your transcripts...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Your Transcript History</h1>
        <p>View and manage all your extracted transcripts</p>
      </div>

      {transcripts.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📝</div>
          <h3>No transcripts yet</h3>
          <p>Extract your first transcript to get started</p>
        </div>
      ) : (
        <div className="transcript-grid">
          {transcripts.map((transcript) => (
            <div key={transcript.id} className="transcript-card">
              <div className="transcript-card-header">
                <h3>{transcript.video_title}</h3>
                <div className="transcript-card-actions">
                  <button
                    onClick={() => downloadTranscript(transcript)}
                    className="icon-btn"
                    title="Download"
                  >
                    💾
                  </button>
                  <button
                    onClick={() => deleteTranscript(transcript.id)}
                    className="icon-btn"
                    title="Delete"
                  >
                    🗑️
                  </button>
                </div>
              </div>
              <div className="transcript-card-meta">
                <span>📅 {new Date(transcript.created_at).toLocaleDateString()}</span>
                <span>📝 {transcript.transcript_text.length} characters</span>
              </div>
              <div className="transcript-card-preview">
                {transcript.transcript_text.substring(0, 200)}...
              </div>
              <a
                href={transcript.video_url}
                target="_blank"
                rel="noopener noreferrer"
                className="transcript-card-link"
              >
                View on YouTube →
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
