import React from 'react';

export default function Navbar({ currentView, setView, user, onLogout, onOpenAuth, onNavigateSubmit }) {
  return (
    <header className="navbar">
      <div className="brand" onClick={() => setView(user?.is_admin ? 'admin' : 'dashboard')}>
        <div className="brand-icon">🏛️</div>
        <div>
          <div className="brand-title">Jan Nidhi Spotter</div>
          <div className="brand-subtitle">Ground Verification Network</div>
        </div>
      </div>

      <nav className="nav-menu">
        {/* Citizen Navigation: Dashboard, Verify Ground, My Evidence, Profile. NO Admin Portal link. */}
        {!user?.is_admin && (
          <>
            <button
              className={`nav-btn ${currentView === 'dashboard' ? 'active' : ''}`}
              onClick={() => setView('dashboard')}
            >
              📊 Dashboard
            </button>
            <button
              className={`nav-btn ${currentView === 'submit' ? 'active' : ''}`}
              onClick={onNavigateSubmit}
            >
              📸 Verify Ground
            </button>
            <button
              className={`nav-btn ${currentView === 'submissions' ? 'active' : ''}`}
              onClick={() => {
                if (!user) onOpenAuth();
                else setView('submissions');
              }}
            >
              📁 My Evidence
            </button>
            <button
              className={`nav-btn ${currentView === 'profile' ? 'active' : ''}`}
              onClick={() => {
                if (!user) onOpenAuth();
                else setView('profile');
              }}
            >
              👤 Profile
            </button>
          </>
        )}

        {/* Admin Navigation — only visible if user is logged in as admin */}
        {user?.is_admin && (
          <button
            className={`nav-btn ${currentView === 'admin' ? 'active' : ''}`}
            onClick={() => setView('admin')}
          >
            🛡️ Admin Portal
          </button>
        )}

        {user ? (
          <div className="user-nav-box">
            {!user.is_admin && (
              <>
                <span className="level-badge">Lvl {user.level || 1}</span>
                <span className="xp-pill">{user.xp || 0} XP</span>
              </>
            )}
            {user.is_admin && (
              <span className="level-badge" style={{ background: 'linear-gradient(135deg, #f43f5e, #be123c)', color: '#fff' }}>
                ADMIN
              </span>
            )}
            <button
              className="btn btn-secondary"
              style={{ padding: '6px 12px', fontSize: '0.85rem' }}
              onClick={onLogout}
            >
              Logout
            </button>
          </div>
        ) : (
          <button
            className="btn btn-primary"
            style={{ padding: '8px 18px', fontSize: '0.85rem' }}
            onClick={onOpenAuth}
          >
            Login / Register
          </button>
        )}
      </nav>
    </header>
  );
}
