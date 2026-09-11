import React, { useState } from 'react';
import api from '../api';

export default function AdminLogin({ onAuthSuccess, onNavigateHome }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleAdminLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await api.post('/auth/login', { email, password });
      if (!res.data.user?.is_admin) {
        setError('Access denied. This account does not have administrator privileges.');
        return;
      }
      localStorage.setItem('token', res.data.access_token);
      onAuthSuccess(res.data.user);
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid administrator credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '440px', margin: '40px auto' }}>
      <div className="card" style={{ borderTop: '4px solid var(--accent-rose)', padding: '36px' }}>
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '8px' }}>🛡️</div>
          <h2 style={{ fontSize: '1.6rem', fontWeight: 800 }}>Admin Portal Login</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '4px' }}>
            Restricted access for verification administrators
          </p>
        </div>

        {error && <div className="error-banner" style={{ marginBottom: '20px' }}>{error}</div>}

        <form onSubmit={handleAdminLogin}>
          <div className="form-group">
            <label className="form-label">Email / Admin ID</label>
            <input
              type="text"
              className="form-input"
              placeholder="Enter administrator email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="username"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              type="password"
              className="form-input"
              placeholder="Enter password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', padding: '12px', background: 'linear-gradient(135deg, #e11d48, #be123c)', marginTop: '8px' }}
            disabled={loading}
          >
            {loading ? 'Authenticating...' : 'Sign In to Admin Portal'}
          </button>
        </form>

        <div style={{ marginTop: '24px', textAlign: 'center' }}>
          <button
            type="button"
            onClick={onNavigateHome}
            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '0.85rem', cursor: 'pointer', textDecoration: 'underline' }}
          >
            &larr; Return to Citizen Portal
          </button>
        </div>
      </div>
    </div>
  );
}
