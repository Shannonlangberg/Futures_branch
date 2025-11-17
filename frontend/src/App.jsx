import React, { useState, useEffect, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './components/MainLayout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import LogStats from './pages/LogStats';
import Finance from './pages/Finance';
import CampusManagement from './pages/CampusManagement';
import UserManagement from './pages/UserManagement';
import DataExport from './pages/DataExport';
import MyProfile from './pages/MyProfile';
import Passport from './pages/Passport';
import Resources from './pages/Resources';
import ResourceManager from './pages/ResourceManager';
import Heartbeat from './pages/Heartbeat';
import People from './pages/People';
import PersonHealthReport from './pages/PersonHealthReport';
import Landing from './pages/Landing';

const RESOURCE_ALLOWED_ROLES = ['admin'];

const DriveAuthModal = ({ onConnect, connecting, error }) => {
  return (
    <div className="fixed inset-0 z-[1000] flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 border border-white/10 rounded-3xl shadow-2xl max-w-lg w-full p-8 space-y-6">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-purple-500/20 flex items-center justify-center text-3xl">
            🔐
          </div>
          <div>
            <h2 className="text-white text-2xl font-semibold">Connect Google Drive</h2>
            <p className="text-white/70 text-sm">
              Futures PULSE needs access to the shared Drive folders before you continue. Authorise with your Futures Church Google account to unlock Resources.
            </p>
          </div>
        </div>

        <div className="bg-white/5 border border-white/10 rounded-2xl px-4 py-3 text-white/70 text-sm">
          You&apos;ll see a Google popup in a new window. If nothing happens, allow popups for <span className="text-white font-semibold">futures-pulse-production.up.railway.app</span> and try again.
        </div>

        {error && (
          <div className="bg-red-900/30 border border-red-500/40 text-red-200 rounded-2xl px-4 py-3 text-sm">
            {error}
          </div>
        )}

        <button
          type="button"
          onClick={onConnect}
          disabled={connecting}
          className={`w-full inline-flex items-center justify-center gap-3 px-5 py-3 rounded-2xl font-semibold transition-all duration-300
            ${connecting ? 'bg-blue-500/40 text-white/70 cursor-not-allowed' : 'bg-gradient-to-r from-blue-500 to-purple-500 text-white hover:scale-105'}
          `}
        >
          <span className="text-xl">🔗</span>
          {connecting ? 'Opening Google...' : 'Connect with Google'}
        </button>
      </div>
    </div>
  );
};

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [needsDriveAuth, setNeedsDriveAuth] = useState(false);
  const [showDriveModal, setShowDriveModal] = useState(false);
  const [driveConnecting, setDriveConnecting] = useState(false);
  const [driveError, setDriveError] = useState('');
  const [userRole, setUserRole] = useState(null);

  const checkAuthStatus = useCallback(async () => {
    try {
      const response = await fetch('/api/session', {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setIsAuthenticated(data.authenticated);
        const role = data.role || null;
        setUserRole(role);
        const allowsDriveAuth = role ? RESOURCE_ALLOWED_ROLES.includes(role) : false;
        const requiresDrive = allowsDriveAuth && Boolean(data.needs_drive_auth);
        setNeedsDriveAuth(requiresDrive);
        setShowDriveModal(requiresDrive);
        return true;
      } else {
        setIsAuthenticated(false);
        setUserRole(null);
        setNeedsDriveAuth(false);
        setShowDriveModal(false);
        return false;
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setIsAuthenticated(false);
      setUserRole(null);
      setNeedsDriveAuth(false);
      setShowDriveModal(false);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuthStatus();
    
    // Check if we're returning from mobile OAuth redirect
    const oauthInProgress = sessionStorage.getItem('google_oauth_in_progress');
    if (oauthInProgress) {
      sessionStorage.removeItem('google_oauth_in_progress');
      // Wait a moment for session to be updated, then check auth
      setTimeout(() => {
        checkAuthStatus().then(() => {
          setNeedsDriveAuth(false);
          setShowDriveModal(false);
        });
      }, 1000);
    }
  }, [checkAuthStatus]);

  const handleLogin = () => {
    setIsAuthenticated(true);
    setIsLoading(true);
    checkAuthStatus();
  };

  const handleLogout = async () => {
    try {
      await fetch('/api/logout', {
        method: 'POST',
        credentials: 'include'
      });
    } catch (error) {
      console.error('Logout failed:', error);
    }
    setIsAuthenticated(false);
    setUserRole(null);
    setNeedsDriveAuth(false);
    setShowDriveModal(false);
    setDriveError('');
  };

  const handleDriveConnect = useCallback(async () => {
    try {
      setDriveError('');
      setDriveConnecting(true);

      const response = await fetch('/api/google/auth-url', {
        credentials: 'include'
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        const errorMsg = payload.error || 'Unable to begin Google authentication. Please try again.';
        
        // If OAuth is disabled, show a more helpful message
        if (response.status === 503 && errorMsg.includes('disabled')) {
          setDriveError('Google Drive integration needs to be enabled. Please contact your administrator.');
        } else {
          setDriveError(errorMsg);
        }
        setDriveConnecting(false);
        return;
      }

      const data = await response.json();
      const authUrl = data.auth_url || data.authUrl;
      if (!authUrl) {
        setDriveError('Missing Google authentication URL.');
        setDriveConnecting(false);
        return;
      }

      // Detect mobile devices
      const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent) || 
                      (window.innerWidth <= 768 && window.innerHeight <= 1024);
      
      if (isMobile) {
        // On mobile, use full-page redirect instead of popup
        // Store that we're doing OAuth so we can check on return
        sessionStorage.setItem('google_oauth_in_progress', 'true');
        window.location.href = authUrl;
        return; // Don't set connecting to false - we're navigating away
      }

      // On desktop, use popup
      const authWindow = window.open(
        authUrl,
        'googleDriveAuth',
        'width=520,height=680,noopener,noreferrer'
      );

      if (!authWindow) {
        setDriveError('Popup blocked. Please allow popups for this site and try again.');
        setDriveConnecting(false);
        return;
      }

      authWindow.focus();

      // Poll for window closure or success message
      const checkWindow = setInterval(() => {
        if (authWindow.closed) {
          clearInterval(checkWindow);
          setDriveConnecting(false);

          // After the popup is closed, always re-check auth
          // and then hide the modal so the user doesn't need
          // to manually refresh.
          setTimeout(() => {
            checkAuthStatus().finally(() => {
              setNeedsDriveAuth(false);
              setShowDriveModal(false);
              setDriveError('');
            });
          }, 800);
        }
      }, 500);

      // Cleanup interval after 5 minutes
      setTimeout(() => {
        clearInterval(checkWindow);
        if (!authWindow.closed) {
          setDriveConnecting(false);
        }
      }, 300000);
    } catch (error) {
      setDriveError(error.message || 'Unable to begin Google authentication.');
      setDriveConnecting(false);
    }
  }, [checkAuthStatus]);

  useEffect(() => {
    const handleMessage = (event) => {
      // Allow messages from the same origin or from Railway domain
      const allowedOrigins = [
        window.location.origin,
        'https://futures-pulse-production.up.railway.app',
        'https://futures.pulse.com'
      ];
      
      if (!allowedOrigins.some(origin => event.origin === origin || event.origin.startsWith(origin))) {
        return;
      }

      if (event.data && event.data.type === 'googleAuthSuccess') {
        setDriveConnecting(false);
        setDriveError('');
        
        // Immediately check auth status
        checkAuthStatus().then(() => {
          // Close modal after confirming auth
          setTimeout(() => {
            setNeedsDriveAuth(false);
            setShowDriveModal(false);
          }, 500);
        });
      }
    };

    window.addEventListener('message', handleMessage);
    return () => {
      window.removeEventListener('message', handleMessage);
    };
  }, [checkAuthStatus]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <Router>
      {isAuthenticated && showDriveModal && (
        <DriveAuthModal
          onConnect={handleDriveConnect}
          connecting={driveConnecting}
          error={driveError}
        />
      )}
      <Routes>
        <Route 
          path="/login" 
          element={
            isAuthenticated ? 
            <Navigate to="/" replace /> : 
            <Login onLogin={handleLogin} />
          } 
        />
        
        <Route
          path="/*"
          element={
            isAuthenticated ? (
              <MainLayout onLogout={handleLogout}>
                <Routes>
                  <Route path="/" element={<Landing />} />
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/stats" element={<LogStats />} />
                  <Route path="/finance" element={<Finance />} />
                  <Route path="/passport" element={<Passport />} />
                  {userRole && RESOURCE_ALLOWED_ROLES.includes(userRole) && (
                    <>
                      <Route path="/resources" element={<Resources />} />
                      <Route path="/resources/manage" element={<ResourceManager />} />
                    </>
                  )}
                  <Route path="/heartbeat" element={<Heartbeat />} />
                  <Route path="/people" element={<People />} />
                  <Route path="/persons/:personId" element={<PersonHealthReport />} />
                  <Route path="/campuses" element={<CampusManagement />} />
                  <Route path="/users" element={<UserManagement />} />
                  <Route path="/export" element={<DataExport />} />
                  <Route path="/profile" element={<MyProfile />} />
                  <Route path="/settings" element={<Navigate to="/profile" replace />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </MainLayout>
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
