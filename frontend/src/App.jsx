import React, { useState, useEffect } from 'react';
import api from './api';
import Navbar from './components/Navbar';
import AuthModal from './components/AuthModal';
import Dashboard from './pages/Dashboard';
import VerificationForm from './pages/VerificationForm';
import SuccessScreen from './pages/SuccessScreen';
import MySubmissions from './pages/MySubmissions';
import Profile from './pages/Profile';
import AdminDashboard from './pages/AdminDashboard';
import AdminLogin from './pages/AdminLogin';

export default function App() {
  const [currentView, setView] = useState('dashboard');
  const [user, setUser] = useState(null);
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [lastSubmission, setLastSubmission] = useState(null);
  const [pendingRedirect, setPendingRedirect] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      fetchCurrentUser();
    }
  }, []);

  const fetchCurrentUser = async () => {
    try {
      const res = await api.get('/auth/me');
      setUser(res.data);
      if (res.data.is_admin) {
        setView('admin');
      }
    } catch (err) {
      console.warn('Session expired or invalid token');
      localStorage.removeItem('token');
      setUser(null);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setUser(null);
    setView('dashboard');
  };

  const handleAuthSuccess = (authenticatedUser) => {
    setUser(authenticatedUser);
    setIsAuthOpen(false);

    if (authenticatedUser.is_admin) {
      setView('admin');
      setPendingRedirect(null);
    } else if (pendingRedirect) {
      setView(pendingRedirect);
      setPendingRedirect(null);
    } else {
      setView('dashboard');
    }
  };

  // Protected navigation: Verify Ground requires login
  const navigateToSubmit = () => {
    if (!user) {
      setPendingRedirect('submit');
      setIsAuthOpen(true);
    } else {
      setView('submit');
    }
  };

  const handleSubmissionSuccess = (submissionData) => {
    setLastSubmission(submissionData);
    setView('success');
  };

  return (
    <div className="app-container" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar
        currentView={currentView}
        setView={setView}
        user={user}
        onLogout={handleLogout}
        onOpenAuth={() => setIsAuthOpen(true)}
        onNavigateSubmit={navigateToSubmit}
      />

      <main style={{ flex: 1 }}>
        {/* Welcome banner for unauthenticated visitors on dashboard */}
        {!user && currentView === 'dashboard' && (
          <div className="card" style={{ textAlign: 'center', padding: '40px 20px', marginBottom: '32px' }}>
            <h2 style={{ fontSize: '1.8rem', fontWeight: 800, marginBottom: '8px' }}>
              Citizen-Powered Public Works Monitoring
            </h2>
            <p style={{ color: 'var(--text-secondary)', maxWidth: '600px', margin: '0 auto 20px auto' }}>
              Log in or register to submit ground photographic evidence and verify public works.
              Verified submissions earn <strong>+150 XP</strong> after admin approval.
            </p>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
              <button
                className="btn btn-primary"
                onClick={() => {
                  setPendingRedirect('submit');
                  setIsAuthOpen(true);
                }}
              >
                📸 Verify Ground
              </button>
              <button className="btn btn-secondary" onClick={() => setIsAuthOpen(true)}>
                Login / Register
              </button>
            </div>
          </div>
        )}

        {/* View Routing */}
        {currentView === 'dashboard' && (
          <Dashboard
            user={user}
            onNavigateSubmit={navigateToSubmit}
          />
        )}

        {/* Route guard: submit requires login */}
        {currentView === 'submit' && (
          user ? (
            <VerificationForm
              user={user}
              onSuccess={handleSubmissionSuccess}
            />
          ) : (
            <div className="card" style={{ textAlign: 'center', padding: '60px', maxWidth: '500px', margin: '40px auto' }}>
              <div style={{ fontSize: '2.5rem', marginBottom: '12px' }}>🔒</div>
              <h3 style={{ marginBottom: '12px' }}>Login Required</h3>
              <p style={{ color: 'var(--text-secondary)', marginBottom: '20px' }}>
                You must be logged in to submit a ground verification.
              </p>
              <button
                className="btn btn-primary"
                onClick={() => {
                  setPendingRedirect('submit');
                  setIsAuthOpen(true);
                }}
              >
                Login / Register to Continue
              </button>
            </div>
          )
        )}

        {currentView === 'success' && (
          <SuccessScreen
            verification={lastSubmission}
            onNavigateDashboard={() => setView('dashboard')}
            onNavigateSubmissions={() => setView('submissions')}
          />
        )}

        {currentView === 'submissions' && (
          user ? (
            <MySubmissions
              onNavigateSubmit={navigateToSubmit}
            />
          ) : (
            <div className="card" style={{ textAlign: 'center', padding: '60px', maxWidth: '500px', margin: '40px auto' }}>
              <div style={{ fontSize: '2.5rem', marginBottom: '12px' }}>🔒</div>
              <h3 style={{ marginBottom: '12px' }}>Login Required</h3>
              <p style={{ color: 'var(--text-secondary)', marginBottom: '20px' }}>
                Please log in to inspect your submitted ground evidence and tracking status.
              </p>
              <button className="btn btn-primary" onClick={() => setIsAuthOpen(true)}>
                Login to View Evidence
              </button>
            </div>
          )
        )}

        {currentView === 'profile' && (
          user ? (
            <Profile
              user={user}
              onLogout={handleLogout}
              onNavigateSubmit={navigateToSubmit}
            />
          ) : (
            <div className="card" style={{ textAlign: 'center', padding: '60px', maxWidth: '500px', margin: '40px auto' }}>
              <div style={{ fontSize: '2.5rem', marginBottom: '12px' }}>🔒</div>
              <h3 style={{ marginBottom: '12px' }}>Login Required</h3>
              <p style={{ color: 'var(--text-secondary)', marginBottom: '20px' }}>
                Please log in to view your citizen profile and XP progression.
              </p>
              <button className="btn btn-primary" onClick={() => setIsAuthOpen(true)}>
                Login / Register
              </button>
            </div>
          )
        )}

        {/* Admin Dashboard — restricted to authenticated admins */}
        {currentView === 'admin' && (
          user?.is_admin ? (
            <AdminDashboard />
          ) : (
            <AdminLogin
              onAuthSuccess={handleAuthSuccess}
              onNavigateHome={() => setView('dashboard')}
            />
          )
        )}

        {/* Dedicated Admin Login page */}
        {currentView === 'admin-login' && (
          <AdminLogin
            onAuthSuccess={handleAuthSuccess}
            onNavigateHome={() => setView('dashboard')}
          />
        )}
      </main>

      {/* Footer with subtle Admin Login link */}
      <footer style={{ marginTop: 'auto', borderTop: '1px solid var(--border-color)', padding: '20px 0', textAlign: 'center', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
        <div>
          Jan Nidhi Spotter &bull; Citizen Ground Verification & Civic Accountability Network
        </div>
        <div style={{ marginTop: '6px' }}>
          {!user?.is_admin && (
            <button
              type="button"
              onClick={() => setView('admin-login')}
              style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '0.75rem', cursor: 'pointer', opacity: 0.6 }}
            >
              Administrator Access
            </button>
          )}
        </div>
      </footer>

      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        onAuthSuccess={handleAuthSuccess}
      />
    </div>
  );
}
