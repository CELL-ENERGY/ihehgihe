import React, { useEffect, useState } from 'react';
import api from '../api';

export default function MySubmissions({ onNavigateSubmit }) {
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSubmissions();
  }, []);

  const fetchSubmissions = async () => {
    try {
      const res = await api.get('/users/me/submissions');
      setSubmissions(res.data);
    } catch (err) {
      console.error('Error fetching submissions:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusDisplay = (statusStr) => {
    const s = (statusStr || '').toUpperCase();
    if (s === 'VERIFIED') {
      return {
        label: 'Verified',
        className: 'status-badge status-verified',
        xpText: '+150 XP',
        xpColor: 'var(--accent-emerald)',
      };
    } else if (s === 'REJECTED') {
      return {
        label: 'Rejected',
        className: 'status-badge status-rejected',
        xpText: '0 XP',
        xpColor: 'var(--accent-rose)',
      };
    } else if (s === 'UNDER_REVIEW') {
      return {
        label: 'Under Review',
        className: 'status-badge status-under-review',
        xpText: 'Not awarded yet',
        xpColor: 'var(--text-muted)',
      };
    } else {
      return {
        label: 'Pending Review',
        className: 'status-badge status-pending',
        xpText: 'Not awarded yet',
        xpColor: 'var(--text-muted)',
      };
    }
  };

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-secondary)' }}>Loading your ground evidence...</div>;
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h2 style={{ fontSize: '1.6rem', fontWeight: 800 }}>My Evidence</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            History of photographic evidence you contributed to the civic ledger
          </p>
        </div>
        <button className="btn btn-primary" onClick={onNavigateSubmit}>
          + New Verification
        </button>
      </div>

      {submissions.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '60px' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '12px' }}>📷</div>
          <h3>No ground verifications yet</h3>
          <p style={{ color: 'var(--text-secondary)', marginTop: '4px', marginBottom: '16px' }}>
            Spot a public work in your locality and earn 150 XP upon admin approval!
          </p>
          <button className="btn btn-primary" onClick={onNavigateSubmit}>Submit First Verification</button>
        </div>
      ) : (
        <div className="submissions-grid">
          {submissions.map((item) => {
            const dateStr = new Date(item.created_at).toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'short',
              day: 'numeric',
            });

            const statusInfo = getStatusDisplay(item.review_status);

            return (
              <div key={item.id} className="submission-card">
                <a href={item.image_url} target="_blank" rel="noopener noreferrer">
                  <img
                    src={item.image_url}
                    className="submission-img"
                    alt="Ground Evidence"
                    onError={(e) => { e.target.src = 'https://via.placeholder.com/400x250?text=Ground+Evidence'; }}
                  />
                </a>
                <div className="submission-body">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                    <span className={statusInfo.className}>
                      {statusInfo.label}
                    </span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{dateStr}</span>
                  </div>

                  <h4 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '4px' }}>{item.locality_name}</h4>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                    <strong>{item.structure_type}</strong> &bull; {item.ground_observation}
                  </div>

                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'monospace', marginBottom: '16px' }}>
                    📍 {Number(item.latitude).toFixed(5)}, {Number(item.longitude).toFixed(5)}
                  </div>

                  {item.admin_comment && (
                    <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '8px 12px', borderRadius: '6px', fontSize: '0.8rem', marginBottom: '14px', borderLeft: '3px solid var(--accent-indigo)' }}>
                      <strong>Admin note:</strong> {item.admin_comment}
                    </div>
                  )}

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-color)', paddingTop: '12px' }}>
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                      Status: <strong>{statusInfo.label}</strong>
                    </span>

                    {/* Strict XP display without any manual claim button */}
                    <div style={{ fontSize: '0.85rem', fontWeight: 700, color: statusInfo.xpColor }}>
                      XP: {statusInfo.xpText}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
