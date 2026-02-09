import React, { useState } from 'react';
import { login, register as apiRegister } from '../services/api';
import './ClientAuth.css';

interface Props {
  visible: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const ClientAuth: React.FC<Props> = ({ visible, onClose, onSuccess }) => {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!visible) return null;

  const handleLogin = async () => {
    setError(null);
    if (!email) {
      setError('Please provide an email or username');
      return;
    }
    setLoading(true);
    try {
      await login(email, password);
      onSuccess();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async () => {
    if (!email) {
      setError('Please provide an email or username');
      return;
    }
    if (password !== confirm) {
      setError('Passwords do not match');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await apiRegister(email, password, 'user');
      // auto-login after register
      await login(email, password);
      onSuccess();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="auth-modal" onClick={(e) => e.stopPropagation()}>
        <h2>{mode === 'login' ? '🔐 Client Sign In' : '🆕 Client Register'}</h2>
        <div className="form-group">
          <label>Email (Gmail)</label>
          <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@gmail.com" autoFocus />
        </div>
        <div className="form-group">
          <label>Password</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>
        {mode === 'register' && (
          <div className="form-group">
            <label>Confirm Password</label>
            <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} />
          </div>
        )}

        {error && <p className="auth-error">⚠️ {error}</p>}

        <div className="modal-buttons">
          <button className="cancel-btn" onClick={onClose} disabled={loading}>
            Cancel
          </button>
          {mode === 'login' ? (
            <button className="login-btn" onClick={handleLogin} disabled={loading}>
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          ) : (
            <button className="login-btn" onClick={handleRegister} disabled={loading}>
              {loading ? 'Registering...' : 'Register'}
            </button>
          )}
        </div>

        <div className="auth-toggle">
          {mode === 'login' ? (
            <p>
              Don't have an account?{' '}
              <button className="link-btn" onClick={() => setMode('register')}>
                Create one
              </button>
            </p>
          ) : (
            <p>
              Already have an account?{' '}
              <button className="link-btn" onClick={() => setMode('login')}>
                Sign in
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default ClientAuth;
