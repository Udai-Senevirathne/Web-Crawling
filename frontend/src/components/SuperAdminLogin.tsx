import React, { useState } from 'react';
import { login, getCurrentUser, logout } from '../services/api';
import './ClientAuth.css';

interface Props {
  visible: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const SuperAdminLogin: React.FC<Props> = ({ visible, onClose, onSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!visible) return null;

  const handleLogin = async () => {
    setError(null);
    setLoading(true);
    try {
      await login(username, password);
      const me = await getCurrentUser();
      if (!me || me.role !== 'superadmin') {
        // not a superadmin; log out of the session we just created
        logout();
        setError('Account is not a Super Admin');
      } else {
        onSuccess();
        onClose();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="auth-modal" onClick={(e) => e.stopPropagation()}>
        <h2>🛡️ Super Admin Sign In</h2>
        <div className="form-group">
          <label>Username</label>
          <input value={username} onChange={(e) => setUsername(e.target.value)} />
        </div>
        <div className="form-group">
          <label>Password</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>

        {error && <p className="auth-error">⚠️ {error}</p>}

        <div className="modal-buttons">
          <button className="cancel-btn" onClick={onClose} disabled={loading}>
            Cancel
          </button>
          <button className="login-btn" onClick={handleLogin} disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SuperAdminLogin;
