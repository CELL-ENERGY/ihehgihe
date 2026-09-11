import React from 'react';

export default function SuccessScreen({ verification, onNavigateDashboard, onNavigateSubmissions }) {
  if (!verification) return null;

  return (
    <div className="card success-screen" style={{ maxWidth: '640px', margin: '30px auto', textAlign: 'center', padding: '40px 30px' }}>
      <div className="success-icon" style={{ fontSize: '3rem', color: 'var(--accent-emerald)', marginBottom: '12px' }}>✓</div>
      <h1 className="success-title" style={{ fontSize: '1.8rem', fontWeight: 800, marginBottom: '8px' }}>
        Verification Submitted Successfully!
      </h1>
      <p className="success-subtitle" style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
        Your ground evidence has been securely recorded on the civic ledger.
      </p>

      {/* Evidence Summary Card */}
      <div className="evidence-preview-card" style={{ textAlign: 'left', marginBottom: '24px' }}>
        <img
          src={verification.imageUrl}
          className="evidence-thumb"
          alt="Submitted Ground Evidence"
          onError={(e) => { e.target.src = 'https://via.placeholder.com/300x200?text=Ground+Evidence'; }}
        />
        <div className="evidence-meta">
          <div><strong>Citizen ID:</strong> {verification.citizenHandle}</div>
          <div><strong>Locality:</strong> {verification.localityName}</div>
          <div><strong>Structure:</strong> {verification.structureType}</div>
          <div><strong>Observation:</strong> {verification.groundObservation}</div>
          <div><strong>Location:</strong> <span style={{ fontFamily: 'monospace' }}>{verification.latitude}, {verification.longitude}</span></div>
          <div>
            <strong>Status:</strong> <span className="status-badge status-pending">Pending Review</span>
          </div>
        </div>
      </div>

      {/* Admin Approval Notice Banner (Replaces Claim XP) */}
      <div
        style={{
          background: 'rgba(99, 102, 241, 0.1)',
          border: '1px solid rgba(99, 102, 241, 0.3)',
          borderRadius: '12px',
          padding: '20px',
          marginBottom: '28px',
          textAlign: 'center',
        }}
      >
        <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#a5b4fc', marginBottom: '6px' }}>
          ⏳ Verification Pending Admin Review
        </div>
        <div style={{ fontSize: '0.95rem', color: 'var(--text-secondary)' }}>
          Current XP awarded: <strong style={{ color: '#fff' }}>0 XP</strong>
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '8px', marginBottom: 0 }}>
          An administrator will inspect your submitted ground evidence. Once approved, <strong>+150 XP</strong> will be awarded automatically to your account.
        </p>
      </div>

      <div style={{ display: 'flex', gap: '16px', justifyContent: 'center' }}>
        <button className="btn btn-secondary" onClick={onNavigateDashboard}>
          Return to Dashboard
        </button>
        <button className="btn btn-primary" onClick={onNavigateSubmissions}>
          View My Evidence
        </button>
      </div>
    </div>
  );
}
