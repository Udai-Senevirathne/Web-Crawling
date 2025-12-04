import { useState } from 'react';
import { AdminPanel } from './components/AdminPanel';
import { ClientChat } from './components/ClientChat';
import './App.css';

function App() {
  const [showAdmin, setShowAdmin] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [password, setPassword] = useState('');
  const [loginError, setLoginError] = useState('');

  // Simple admin password (in production, use proper auth)
  const ADMIN_PASSWORD = 'admin123';

  const handleLogin = () => {
    if (password === ADMIN_PASSWORD) {
      setIsLoggedIn(true);
      setShowAdmin(true);
      setShowLoginModal(false);
      setPassword('');
      setLoginError('');
    } else {
      setLoginError('Invalid password');
    }
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setShowAdmin(false);
  };

  const handleAdminClick = () => {
    if (isLoggedIn) {
      setShowAdmin(!showAdmin);
    } else {
      setShowLoginModal(true);
    }
  };

  return (
    <div className="app-container">
      {/* Admin Controls */}
      <div className="admin-button-container">
        {isLoggedIn && showAdmin ? (
          <button className="back-to-chat-btn" onClick={() => setShowAdmin(false)}>
            ← Back to Chat
          </button>
        ) : (
          <button 
            className="admin-trigger-btn" 
            onClick={handleAdminClick} 
            title="Settings"
          >
            ⚙️
          </button>
        )}
      </div>

      {/* Login Modal */}
      {showLoginModal && (
        <div className="modal-overlay" onClick={() => setShowLoginModal(false)}>
          <div className="login-modal" onClick={(e) => e.stopPropagation()}>
            <h2>Admin Access</h2>
            <p>Please enter your credentials to continue</p>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
              placeholder="Enter password"
              autoFocus
            />
            {loginError && <p className="login-error">{loginError}</p>}
            <div className="modal-buttons">
              <button className="cancel-btn" onClick={() => setShowLoginModal(false)}>
                Cancel
              </button>
              <button className="login-btn" onClick={handleLogin}>
                Sign In
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      {showAdmin && isLoggedIn ? <AdminPanel /> : <ClientChat />}
    </div>
  );
}

export default App;

