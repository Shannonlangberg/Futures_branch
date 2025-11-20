import React, { useState, useEffect, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './components/MainLayout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import LogStats from './pages/LogStats';
import Finance from './pages/Finance';
import GivingAnalytics from './pages/GivingAnalytics';
import CampusManagement from './pages/CampusManagement';
import UserManagement from './pages/UserManagement';
import DataExport from './pages/DataExport';
import MyProfile from './pages/MyProfile';
import Passport from './pages/Passport';
import Resources from './pages/Resources';
import ResourceManager from './pages/ResourceManager';
import Heartbeat from './pages/Heartbeat';
import People from './pages/People';
import Lists from './pages/Lists';
import PersonHealthReport from './pages/PersonHealthReport';
import PastoralCareAppointments from './pages/PastoralCareAppointments';
import BeaconManagement from './pages/BeaconManagement';
import PathwayManager from './pages/PathwayManager';
import Landing from './pages/Landing';
import ConnectGroups from './pages/ConnectGroups';
import ConnectGroupLeader from './pages/ConnectGroupLeader';
import Give from './pages/Give';
import TV from './pages/TV';
import TVSeries from './pages/TVSeries';
import TVWatch from './pages/TVWatch';
import TVManager from './pages/TVManager';

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
  const [railwayBranch, setRailwayBranch] = useState(null);

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
        // Default to 'beta' (show all features) unless explicitly 'main'
        setRailwayBranch(data.railway_branch || 'beta');
        const allowsDriveAuth = role ? RESOURCE_ALLOWED_ROLES.includes(role) : false;
        const requiresDrive = allowsDriveAuth && Boolean(data.needs_drive_auth);
        setNeedsDriveAuth(requiresDrive);
        setShowDriveModal(requiresDrive);
        return true;
      } else {
        setIsAuthenticated(false);
        setUserRole(null);
        setRailwayBranch(null);
        setNeedsDriveAuth(false);
        setShowDriveModal(false);
        return false;
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setIsAuthenticated(false);
      setUserRole(null);
      setRailwayBranch(null);
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
    const oauthSuccess = sessionStorage.getItem('google_oauth_success');
    const urlParams = new URLSearchParams(window.location.search);
    const oauthSuccessParam = urlParams.get('oauth_success');
    
    if (oauthInProgress || oauthSuccess || oauthSuccessParam) {
      sessionStorage.removeItem('google_oauth_in_progress');
      sessionStorage.removeItem('google_oauth_success');
      
      // Clean up URL parameter
      if (oauthSuccessParam) {
        window.history.replaceState({}, '', window.location.pathname);
      }
      
      // Wait a moment for session to be updated, then check auth multiple times
      // This ensures the session cookie is properly set
      let attempts = 0;
      const maxAttempts = 5;
      
      const checkAuthWithRetry = () => {
        attempts++;
        fetch('/api/session', { credentials: 'include' })
          .then(res => res.json())
          .then((sessionData) => {
            if (sessionData && sessionData.authenticated) {
              setIsAuthenticated(true);
              setNeedsDriveAuth(false);
              setShowDriveModal(false);
              setDriveError('');
              
              // Force a page refresh to ensure all components see the new auth state
              if (attempts === 1) {
                // Only refresh on first successful check
                setTimeout(() => {
                  window.location.reload();
                }, 500);
              }
            } else if (attempts < maxAttempts) {
              // Retry if not authenticated yet
              setTimeout(checkAuthWithRetry, 500);
            }
          }).catch(() => {
            if (attempts < maxAttempts) {
              setTimeout(checkAuthWithRetry, 500);
            }
          });
      };
      
      setTimeout(checkAuthWithRetry, 1000);
    }
  }, [checkAuthStatus]);
  
  useEffect(() => {
    // Listen for OAuth success messages (from popup or redirect)
    const handleMessage = (event) => {
      // Accept messages from same origin
      if (event.origin !== window.location.origin) {
        return;
      }
      
      if (event.data && event.data.type === 'googleAuthSuccess') {
        // OAuth completed successfully - close modal and refresh page
        setNeedsDriveAuth(false);
        setShowDriveModal(false);
        setDriveError('');
        setDriveConnecting(false);
        
        // Refresh the page to ensure all components see the updated auth state
        setTimeout(() => {
          window.location.reload();
        }, 300);
      }
    };
    
    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
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

          // After the popup is closed, close modal and refresh page
          setNeedsDriveAuth(false);
          setShowDriveModal(false);
          setDriveError('');
          
          // Refresh the page to ensure all components see the updated auth state
          setTimeout(() => {
            window.location.reload();
          }, 500);
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
    // This handler is for the Drive auth modal specifically
    const handleDriveAuthMessage = (event) => {
      // Allow messages from the same origin
      const allowedOrigins = [
        window.location.origin,
        'https://futures-pulse-production.up.railway.app',
        'https://futures.pulse.com'
      ];
      
      if (!allowedOrigins.some(origin => event.origin === origin || event.origin.startsWith(origin))) {
        return;
      }

      if (event.data && event.data.type === 'googleAuthSuccess') {
        // OAuth completed successfully - close modal and refresh page
        setDriveConnecting(false);
        setDriveError('');
        setNeedsDriveAuth(false);
        setShowDriveModal(false);
        
        // Refresh the page to ensure all components see the updated auth state
        setTimeout(() => {
          window.location.reload();
        }, 300);
      }
    };

    window.addEventListener('message', handleDriveAuthMessage);
    return () => {
      window.removeEventListener('message', handleDriveAuthMessage);
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
        
        {/* Connect Group Leader Portal - Standalone (no MainLayout) */}
        <Route path="/connect-group-leader" element={<ConnectGroupLeader />} />
        
        {/* Public Give Page - No auth required */}
        <Route path="/give" element={<Give />} />
        
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
                  <Route path="/giving-analytics" element={<GivingAnalytics />} />
                  <Route path="/passport" element={<Passport />} />
                  {userRole && RESOURCE_ALLOWED_ROLES.includes(userRole) && (
                    <>
                      <Route path="/resources" element={<Resources />} />
                      <Route path="/resources/manage" element={<ResourceManager />} />
                    </>
                  )}
                  <Route path="/heartbeat" element={<Heartbeat />} />
                  <Route path="/people" element={<People />} />
                  <Route path="/lists" element={<Lists />} />
                  <Route path="/connect-groups" element={<ConnectGroups />} />
                  <Route path="/persons/:personId" element={<PersonHealthReport />} />
                  <Route path="/pastoral-care" element={<PastoralCareAppointments />} />
                  <Route path="/campuses" element={<CampusManagement />} />
                  <Route path="/users" element={<UserManagement />} />
                  <Route path="/export" element={<DataExport />} />
                  <Route path="/beacons" element={<BeaconManagement />} />
                  <Route path="/pathways" element={<PathwayManager />} />
                  <Route path="/profile" element={<MyProfile />} />
                  <Route path="/settings" element={<Navigate to="/profile" replace />} />
                  <Route path="/tv" element={<TV />} />
                  <Route path="/tv/series/:id" element={<TVSeries />} />
                  <Route path="/tv/watch/:episodeId" element={<TVWatch />} />
                  <Route path="/tv/manage" element={<TVManager />} />
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
