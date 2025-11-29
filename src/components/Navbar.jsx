import { useAuth } from '../contexts/AuthContext';

export default function Navbar({ currentPage, onNavigate }) {
  const { user, profile, signOut } = useAuth();

  const handleSignOut = async () => {
    await signOut();
    onNavigate('home');
  };

  return (
    <nav className="navbar">
      <div className="nav-container">
        <div className="nav-brand" onClick={() => onNavigate('home')}>
          🎙️ VideoTranscript Pro
        </div>
        <div className="nav-links">
          <button
            className={`nav-link ${currentPage === 'home' ? 'active' : ''}`}
            onClick={() => onNavigate('home')}
          >
            Home
          </button>
          {user && (
            <>
              <button
                className={`nav-link ${currentPage === 'history' ? 'active' : ''}`}
                onClick={() => onNavigate('history')}
              >
                History
              </button>
              <button
                className={`nav-link ${currentPage === 'podcasts' ? 'active' : ''}`}
                onClick={() => onNavigate('podcasts')}
              >
                Podcasts
              </button>
            </>
          )}
          <button
            className={`nav-link ${currentPage === 'api' ? 'active' : ''}`}
            onClick={() => onNavigate('api')}
          >
            API
          </button>
          <button
            className={`nav-link ${currentPage === 'pricing' ? 'active' : ''}`}
            onClick={() => onNavigate('pricing')}
          >
            Pricing
          </button>
          {user ? (
            <>
              <div className="nav-tokens">
                {profile?.tokens || 0} tokens
              </div>
              <button className="nav-link" onClick={handleSignOut}>
                Sign Out
              </button>
            </>
          ) : (
            <button
              className="nav-link-btn"
              onClick={() => onNavigate('login')}
            >
              Sign In
            </button>
          )}
        </div>
      </div>
    </nav>
  );
}
