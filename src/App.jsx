import { useState } from 'react';
import { AuthProvider } from './contexts/AuthContext';
import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import HistoryPage from './pages/HistoryPage';
import PodcastsPage from './pages/PodcastsPage';
import ApiPage from './pages/ApiPage';
import PricingPage from './pages/PricingPage';
import VideoPage from './pages/VideoPage';

function App() {
  const [currentPage, setCurrentPage] = useState('home');
  const [currentVideoId, setCurrentVideoId] = useState(null);

  const navigateToVideo = (videoId) => {
    setCurrentVideoId(videoId);
    setCurrentPage('video');
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'home':
        return <HomePage onNavigate={setCurrentPage} onVideoClick={navigateToVideo} />;
      case 'login':
        return <LoginPage onNavigate={setCurrentPage} />;
      case 'history':
        return <HistoryPage onVideoClick={navigateToVideo} />;
      case 'podcasts':
        return <PodcastsPage />;
      case 'api':
        return <ApiPage />;
      case 'pricing':
        return <PricingPage onNavigate={setCurrentPage} />;
      case 'video':
        return <VideoPage videoId={currentVideoId} onNavigate={setCurrentPage} />;
      default:
        return <HomePage onNavigate={setCurrentPage} onVideoClick={navigateToVideo} />;
    }
  };

  return (
    <AuthProvider>
      <div className="app">
        <Navbar currentPage={currentPage} onNavigate={setCurrentPage} />
        <div className="main-content">
          {renderPage()}
        </div>
        <footer className="footer">
          <div className="footer-content">
            <div className="footer-brand">🎙️ VideoTranscript Pro</div>
            <div className="footer-links">
              <button onClick={() => setCurrentPage('home')} className="footer-link">
                Home
              </button>
              <button onClick={() => setCurrentPage('api')} className="footer-link">
                API
              </button>
              <button onClick={() => setCurrentPage('pricing')} className="footer-link">
                Pricing
              </button>
            </div>
            <div className="footer-text">
              © 2024 VideoTranscript Pro. Convert YouTube videos to podcasts.
            </div>
          </div>
        </footer>
      </div>
    </AuthProvider>
  );
}

export default App;
