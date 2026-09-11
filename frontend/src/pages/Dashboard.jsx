import React, { useEffect, useState } from 'react';
import api from '../api';

export default function Dashboard({ user, onNavigateSubmit }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardStats();
  }, [user]);

  const fetchDashboardStats = async () => {
    try {
      const res = await api.get('/users/me/dashboard');
      setStats(res.data);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-secondary)' }}>Loading citizen dashboard...</div>;
  }

  const currentLevel = stats?.current_level ?? user?.level ?? 1;
  const currentXp = stats?.current_xp ?? user?.xp ?? 0;
  const progressPercent = stats?.progress_percent ?? 0;
  const xpNeeded = stats?.xp_to_next_level ?? 300;

  return (
    <div>
      <div className="dashboard-hero">
        <div className="card" style={{ marginBottom: 0 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--accent-emerald)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Citizen Spotter Profile
              </div>
              <h1 style={{ fontSize: '2rem', fontWeight: 800, marginTop: '4px' }}>
                {stats?.name || user?.name || 'Citizen'}
              </h1>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                {stats?.email || user?.email}
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <span className="level-badge" style={{ fontSize: '1rem', padding: '6px 16px' }}>
                Level {currentLevel}
              </span>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f9fafb', marginTop: '8px' }}>
                {currentXp} <span style={{ fontSize: '0.9rem', color: 'var(--accent-amber)' }}>XP</span>
              </div>
            </div>
          </div>

          {/* XP Progression Bar */}
          <div className="xp-progress-box">
            <div className="progress-header">
              <span>Next Level Progression</span>
              <span>{xpNeeded} XP to Level {currentLevel + 1} ({progressPercent}%)</span>
            </div>
            <div className="progress-bar-bg">
              <div className="progress-bar-fill" style={{ width: `${progressPercent}%` }}></div>
            </div>
          </div>
        </div>

        {/* Action Callout */}
        <div
          className="card"
          style={{
            marginBottom: 0,
            background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(16, 185, 129, 0.15))',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            textAlign: 'center',
            borderColor: 'rgba(16, 185, 129, 0.3)',
          }}
        >
          <div style={{ fontSize: '2rem', marginBottom: '8px' }}>📍</div>
          <h3 style={{ fontSize: '1.2rem', marginBottom: '6px' }}>Spot Public Works</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>
            Capture live ground evidence & receive <strong>+150 XP</strong> upon admin verification!
          </p>
          <button className="btn btn-primary" onClick={onNavigateSubmit}>
            Verify Ground
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-number" style={{ color: '#60a5fa' }}>{stats?.total_submissions || 0}</div>
          <div className="stat-label">My Submissions</div>
        </div>
        <div className="stat-card">
          <div className="stat-number" style={{ color: 'var(--accent-amber)' }}>{stats?.pending_submissions || 0}</div>
          <div className="stat-label">Pending Review</div>
        </div>
        <div className="stat-card">
          <div className="stat-number" style={{ color: 'var(--accent-emerald)' }}>{stats?.verified_submissions || 0}</div>
          <div className="stat-label">Verified (+150 XP each)</div>
        </div>
        <div className="stat-card">
          <div className="stat-number" style={{ color: 'var(--accent-rose)' }}>{stats?.rejected_submissions || 0}</div>
          <div className="stat-label">Rejected Submissions</div>
        </div>
      </div>

      {/* Clear Explanation Banners */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginTop: '20px' }}>
        <div className="card" style={{ marginBottom: 0, borderLeft: '4px solid var(--accent-amber)' }}>
          <div style={{ fontWeight: 700, color: 'var(--accent-amber)', marginBottom: '4px' }}>
            ⏳ Pending Submissions ({stats?.pending_submissions || 0})
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', margin: 0 }}>
            XP will be awarded after admin approval.
          </p>
        </div>

        <div className="card" style={{ marginBottom: 0, borderLeft: '4px solid var(--accent-emerald)' }}>
          <div style={{ fontWeight: 700, color: 'var(--accent-emerald)', marginBottom: '4px' }}>
            ✓ Verified Submissions ({stats?.verified_submissions || 0})
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', margin: 0 }}>
            ✓ Verified — 150 XP awarded
          </p>
        </div>
      </div>
    </div>
  );
}
