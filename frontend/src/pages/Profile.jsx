import React, { useEffect, useState } from 'react';
import api from '../api';

export default function Profile({ user, onLogout, onNavigateSubmit }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      fetchProfileStats();
    }
  }, [user]);

  const fetchProfileStats = async () => {
    try {
      const res = await api.get('/users/me/dashboard');
      setStats(res.data);
    } catch (err) {
      console.error('Failed to load profile:', err);
    } finally {
      setLoading(false);
    }
  };

  const currentLevel = stats?.current_level ?? user?.level ?? 1;
  const currentXp = stats?.current_xp ?? user?.xp ?? 0;
  const progressPercent = stats?.progress_percent ?? 0;
  const xpNeeded = stats?.xp_to_next_level ?? 300;

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <div className="card" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px', marginBottom: '24px' }}>
          <div
            style={{
              width: '72px',
              height: '72px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, var(--accent-indigo), var(--accent-emerald))',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '2rem',
              color: '#fff',
              boxShadow: '0 8px 24px rgba(99, 102, 241, 0.3)',
            }}
          >
            👤
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h2 style={{ fontSize: '1.6rem', fontWeight: 800 }}>{stats?.name || user?.name || 'Citizen'}</h2>
              <span className="level-badge">Level {currentLevel}</span>
              {user?.is_admin && (
                <span className="level-badge" style={{ background: '#f43f5e' }}>ADMIN</span>
              )}
            </div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '2px' }}>
              {stats?.email || user?.email}
            </div>
          </div>
          <button className="btn btn-secondary" onClick={onLogout} style={{ padding: '8px 16px', fontSize: '0.85rem' }}>
            Logout
          </button>
        </div>

        {/* XP Progression */}
        <div className="xp-progress-box" style={{ marginTop: '16px' }}>
          <div className="progress-header">
            <span>Level Progress</span>
            <span style={{ fontWeight: 700 }}>
              {currentXp} XP total &bull; {xpNeeded} XP to Level {currentLevel + 1} ({progressPercent}%)
            </span>
          </div>
          <div className="progress-bar-bg">
            <div className="progress-bar-fill" style={{ width: `${progressPercent}%` }}></div>
          </div>
        </div>
      </div>

      {/* Submission & Civic Activity */}
      <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '16px' }}>Civic Contribution Summary</h3>
      <div className="stats-grid" style={{ marginBottom: '24px' }}>
        <div className="stat-card">
          <div className="stat-number" style={{ color: '#60a5fa' }}>{stats?.total_submissions || 0}</div>
          <div className="stat-label">Total Submissions</div>
        </div>
        <div className="stat-card">
          <div className="stat-number" style={{ color: 'var(--accent-emerald)' }}>{stats?.verified_submissions || 0}</div>
          <div className="stat-label">Verified (+150 XP each)</div>
        </div>
        <div className="stat-card">
          <div className="stat-number" style={{ color: 'var(--accent-amber)' }}>{stats?.pending_submissions || 0}</div>
          <div className="stat-label">Pending Admin Review</div>
        </div>
        <div className="stat-card">
          <div className="stat-number" style={{ color: 'var(--accent-rose)' }}>{stats?.rejected_submissions || 0}</div>
          <div className="stat-label">Rejected (0 XP)</div>
        </div>
      </div>

      <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h4 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '4px' }}>Spot More Public Works</h4>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            Contribute ground photographic evidence in your locality. Earn +150 XP upon admin verification.
          </p>
        </div>
        <button className="btn btn-primary" onClick={onNavigateSubmit}>
          + Verify Ground
        </button>
      </div>
    </div>
  );
}
