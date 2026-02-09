
import { useState, useEffect } from 'react';
import { AdminPanel } from './components/AdminPanel';
import { ClientChat } from './components/ClientChat';
import { SettingsPanel } from './components/SettingsPanel';
import { getStats } from './services/api';
import './App.css';

interface Stats {
  total_documents: number;
  model: string;
}

function App() {
  const [activeTab, setActiveTab] = useState<'chat' | 'crawl' | 'settings'>('chat');
  const [stats, setStats] = useState<Stats | null>(null);
  const [chatResetTrigger, setChatResetTrigger] = useState(0);

  useEffect(() => {
    const loadStats = async () => {
      try {
        const data = await getStats();
        setStats(data.stats);
      } catch (err) {
        console.error('Failed to load stats:', err);
      }
    };
    loadStats();
    const interval = setInterval(loadStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleNewChat = () => {
    setChatResetTrigger(prev => prev + 1);
    setActiveTab('chat');
  };

  return (
    <div className="app">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 6v6l4 2" />
            </svg>
            <span>DataCrawl</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <button
            className="nav-item new-chat-action"
            onClick={handleNewChat}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            <span>New Chat</span>
          </button>

          <div className="nav-divider"></div>

          <button
            className={`nav-item ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
            <span>Chat</span>
          </button>
          <button
            className={`nav-item ${activeTab === 'crawl' ? 'active' : ''}`}
            onClick={() => setActiveTab('crawl')}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1 4-10z" />
            </svg>
            <span>Crawl</span>
          </button>
          <button
            className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z" />
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
            </svg>
            <span>Settings</span>
          </button>
        </nav>

        <div className="sidebar-footer">
          <div className="stats-mini">
            <div className="stat-row">
              <span className="stat-label">Indexed</span>
              <span className="stat-value">{stats?.total_documents || 0} docs</span>
            </div>
            <div className="stat-row">
              <span className="stat-label">Model</span>
              <span className="stat-value">{stats?.model?.split('-')[0] || 'Loading'}</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main">
        {activeTab === 'chat' && <ClientChat resetTrigger={chatResetTrigger} />}
        {activeTab === 'crawl' && <AdminPanel />}
        {activeTab === 'settings' && <SettingsPanel />}
      </main>
    </div>
  );
}

export default App;
