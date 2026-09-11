import React, { useEffect, useState } from 'react';
import api from '../api';

export default function AdminDashboard() {
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('PENDING'); // 'ALL' | 'PENDING' | 'UNDER_REVIEW' | 'VERIFIED' | 'REJECTED'
  const [selectedItem, setSelectedItem] = useState(null); // For [ View Evidence ] modal
  const [adminComment, setAdminComment] = useState('');
  const [showApproveConfirm, setShowApproveConfirm] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [toast, setToast] = useState('');

  useEffect(() => {
    fetchAdminVerifications();
  }, []);

  const fetchAdminVerifications = async () => {
    try {
      const res = await api.get('/admin/verifications');
      setSubmissions(res.data);
    } catch (err) {
      console.error('Error fetching admin data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenReview = (item) => {
    setSelectedItem(item);
    setAdminComment(item.admin_comment || '');
    setShowApproveConfirm(false);
  };

  const handleCloseReview = () => {
    setSelectedItem(null);
    setAdminComment('');
    setShowApproveConfirm(false);
  };

  const handleExecuteDecision = async (statusVal) => {
    if (!selectedItem) return;
    setActionLoading(true);
    try {
      const res = await api.patch(`/admin/verifications/${selectedItem.id}`, {
        status: statusVal,
        admin_comment: adminComment,
      });

      setToast(
        statusVal === 'VERIFIED'
          ? `✓ Verification #${selectedItem.id} approved! 150 XP awarded to citizen.`
          : `Decision saved: #${selectedItem.id} set to ${statusVal}.`
      );

      // Update local state
      setSubmissions((prev) =>
        prev.map((s) =>
          s.id === selectedItem.id
            ? {
                ...s,
                review_status: statusVal,
                admin_comment: adminComment,
                xp_awarded: statusVal === 'VERIFIED' ? 150 : (statusVal === 'REJECTED' ? 0 : s.xp_awarded),
                xp_claimed: statusVal === 'VERIFIED' ? true : s.xp_claimed,
              }
            : s
        )
      );

      handleCloseReview();
    } catch (err) {
      setToast(err.response?.data?.detail || 'Failed to submit review decision.');
    } finally {
      setActionLoading(false);
      setTimeout(() => setToast(''), 5000);
    }
  };

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-secondary)' }}>Loading Admin Portal registry...</div>;
  }

  // Counts for tabs
  const countPending = submissions.filter((s) => (s.review_status || '').toUpperCase() === 'PENDING').length;
  const countUnderReview = submissions.filter((s) => (s.review_status || '').toUpperCase() === 'UNDER_REVIEW').length;
  const countVerified = submissions.filter((s) => (s.review_status || '').toUpperCase() === 'VERIFIED').length;
  const countRejected = submissions.filter((s) => (s.review_status || '').toUpperCase() === 'REJECTED').length;

  const filteredSubmissions = submissions.filter((item) => {
    const s = (item.review_status || '').toUpperCase();
    if (activeTab === 'ALL') return true;
    if (activeTab === 'PENDING') return s === 'PENDING';
    if (activeTab === 'UNDER_REVIEW') return s === 'UNDER_REVIEW' || s === 'UNDER REVIEW';
    if (activeTab === 'VERIFIED') return s === 'VERIFIED';
    if (activeTab === 'REJECTED') return s === 'REJECTED';
    return true;
  });

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.6rem', fontWeight: 800 }}>Admin Verification Portal</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          Inspect ground photographic evidence submitted by citizens & allocate XP rewards
        </p>
      </div>

      {toast && (
        <div className="error-banner" style={{ background: 'rgba(16, 185, 129, 0.2)', borderColor: 'var(--accent-emerald)', color: '#a7f3d0' }}>
          {toast}
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', flexWrap: 'wrap' }}>
        <button
          className={`btn btn-secondary ${activeTab === 'PENDING' ? 'active' : ''}`}
          onClick={() => setActiveTab('PENDING')}
          style={{ padding: '8px 16px' }}
        >
          Pending ({countPending})
        </button>
        <button
          className={`btn btn-secondary ${activeTab === 'UNDER_REVIEW' ? 'active' : ''}`}
          onClick={() => setActiveTab('UNDER_REVIEW')}
          style={{ padding: '8px 16px' }}
        >
          Under Review ({countUnderReview})
        </button>
        <button
          className={`btn btn-secondary ${activeTab === 'VERIFIED' ? 'active' : ''}`}
          onClick={() => setActiveTab('VERIFIED')}
          style={{ padding: '8px 16px' }}
        >
          Verified ({countVerified})
        </button>
        <button
          className={`btn btn-secondary ${activeTab === 'REJECTED' ? 'active' : ''}`}
          onClick={() => setActiveTab('REJECTED')}
          style={{ padding: '8px 16px' }}
        >
          Rejected ({countRejected})
        </button>
        <button
          className={`btn btn-secondary ${activeTab === 'ALL' ? 'active' : ''}`}
          onClick={() => setActiveTab('ALL')}
          style={{ padding: '8px 16px' }}
        >
          All ({submissions.length})
        </button>
      </div>

      {filteredSubmissions.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '60px' }}>
          <h3>No verifications in "{activeTab}" category</h3>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {filteredSubmissions.map((item) => {
            const rawStatus = (item.review_status || '').toUpperCase();
            const badgeClass =
              rawStatus === 'VERIFIED'
                ? 'status-badge status-verified'
                : rawStatus === 'REJECTED'
                ? 'status-badge status-rejected'
                : rawStatus === 'UNDER_REVIEW'
                ? 'status-badge status-under-review'
                : 'status-badge status-pending';

            return (
              <div key={item.id} className="card" style={{ marginBottom: 0 }}>
                <div style={{ display: 'grid', gridTemplateColumns: '180px 1fr auto', gap: '20px', alignItems: 'center' }}>
                  {/* Photo thumbnail */}
                  <div>
                    <img
                      src={item.image_url}
                      alt="Ground Evidence"
                      style={{
                        width: '100%',
                        height: '120px',
                        objectFit: 'cover',
                        borderRadius: '8px',
                        border: '1px solid var(--border-color)',
                      }}
                      onError={(e) => { e.target.src = 'https://via.placeholder.com/180x120?text=Photo'; }}
                    />
                  </div>

                  {/* Summary Details */}
                  <div>
                    <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '6px' }}>
                      <span className={badgeClass}>{item.review_status}</span>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {new Date(item.created_at).toLocaleString()}
                      </span>
                      <span style={{ fontSize: '0.85rem', fontWeight: 700, color: item.xp_awarded > 0 ? 'var(--accent-emerald)' : 'var(--text-muted)' }}>
                        {item.xp_awarded > 0 ? `+${item.xp_awarded} XP Awarded` : '0 XP'}
                      </span>
                    </div>

                    <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '4px' }}>
                      {item.locality_name}
                    </h3>

                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                      <strong>Structure:</strong> {item.structure_type} &bull; <strong>Observation:</strong> {item.ground_observation}
                    </div>

                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                      📍 {Number(item.latitude).toFixed(5)}, {Number(item.longitude).toFixed(5)} &bull; ID: {item.citizen_handle}
                    </div>
                  </div>

                  {/* Action */}
                  <div>
                    <button
                      className="btn btn-primary"
                      style={{ padding: '10px 20px', fontSize: '0.9rem', whiteSpace: 'nowrap' }}
                      onClick={() => handleOpenReview(item)}
                    >
                      View Evidence
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* DETAILED REVIEW MODAL */}
      {selectedItem && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: '720px', width: '95%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '1.3rem', fontWeight: 700 }}>
                Verification Evidence Review #{selectedItem.id}
              </h3>
              <button
                onClick={handleCloseReview}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.6rem', cursor: 'pointer' }}
              >
                &times;
              </button>
            </div>

            {/* Photo preview */}
            <div style={{ marginBottom: '16px', textAlign: 'center' }}>
              <a href={selectedItem.image_url} target="_blank" rel="noopener noreferrer">
                <img
                  src={selectedItem.image_url}
                  alt="Full Ground Proof"
                  style={{
                    maxWidth: '100%',
                    maxHeight: '340px',
                    borderRadius: '8px',
                    objectFit: 'contain',
                    border: '1px solid var(--border-color)',
                    background: '#0f172a',
                  }}
                  onError={(e) => { e.target.src = 'https://via.placeholder.com/600x340?text=Ground+Photo'; }}
                />
              </a>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Click image to view full-resolution source ↗
              </div>
            </div>

            {/* Evidence fields table */}
            <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '16px', borderRadius: '8px', marginBottom: '20px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '0.85rem' }}>
              <div><strong>Citizen Handle / ID:</strong> {selectedItem.citizen_handle}</div>
              <div><strong>Account:</strong> {selectedItem.user?.name} ({selectedItem.user?.email})</div>
              <div><strong>Locality:</strong> {selectedItem.locality_name}</div>
              <div><strong>Structure Type:</strong> {selectedItem.structure_type}</div>
              <div><strong>Ground Observation:</strong> {selectedItem.ground_observation}</div>
              <div><strong>GPS Coordinates:</strong> {Number(selectedItem.latitude).toFixed(6)}, {Number(selectedItem.longitude).toFixed(6)}</div>
              <div><strong>Submission Date:</strong> {new Date(selectedItem.created_at).toLocaleString()}</div>
              <div><strong>Current Status:</strong> <span style={{ fontWeight: 700 }}>{selectedItem.review_status}</span></div>
            </div>

            {/* Admin Comment field */}
            <div className="form-group">
              <label className="form-label" style={{ fontSize: '0.85rem' }}>
                Admin Comment / Feedback (Optional)
              </label>
              <input
                type="text"
                className="form-input"
                placeholder="Optional notes or reason for rejection/approval..."
                value={adminComment}
                onChange={(e) => setAdminComment(e.target.value)}
              />
            </div>

            {/* Confirmation Alert when Approve is clicked */}
            {showApproveConfirm ? (
              <div
                style={{
                  background: 'rgba(16, 185, 129, 0.15)',
                  border: '1px solid var(--accent-emerald)',
                  borderRadius: '8px',
                  padding: '16px',
                  marginBottom: '16px',
                  textAlign: 'center',
                }}
              >
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#6ee7b7', marginBottom: '6px' }}>
                  Approve this ground verification?
                </div>
                <p style={{ fontSize: '0.9rem', color: '#a7f3d0', marginBottom: '14px' }}>
                  150 XP will be awarded to the citizen.
                </p>
                <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
                  <button
                    className="btn btn-secondary"
                    onClick={() => setShowApproveConfirm(false)}
                    disabled={actionLoading}
                  >
                    Cancel
                  </button>
                  <button
                    className="btn btn-primary"
                    style={{ background: 'linear-gradient(135deg, #059669, #047857)' }}
                    onClick={() => handleExecuteDecision('VERIFIED')}
                    disabled={actionLoading}
                  >
                    {actionLoading ? 'Approving...' : 'Approve'}
                  </button>
                </div>
              </div>
            ) : (
              /* Review Actions: Approve, Reject, Under Review */
              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', flexWrap: 'wrap' }}>
                <button
                  className="btn btn-secondary"
                  onClick={() => handleExecuteDecision('UNDER_REVIEW')}
                  disabled={actionLoading}
                  style={{ fontSize: '0.85rem' }}
                >
                  Mark Under Review
                </button>
                <button
                  className="btn btn-secondary"
                  style={{ borderColor: 'var(--accent-rose)', color: 'var(--accent-rose)', fontSize: '0.85rem' }}
                  onClick={() => handleExecuteDecision('REJECTED')}
                  disabled={actionLoading}
                >
                  Reject Verification
                </button>
                <button
                  className="btn btn-primary"
                  style={{ background: 'linear-gradient(135deg, #10b981, #059669)', fontSize: '0.85rem' }}
                  onClick={() => setShowApproveConfirm(true)}
                  disabled={actionLoading}
                >
                  Approve Verification
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
