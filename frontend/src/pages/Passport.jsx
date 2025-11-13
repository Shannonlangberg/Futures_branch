import React, { useState, useEffect } from 'react';
import { 
  UserGroupIcon, 
  CheckCircleIcon, 
  ClockIcon,
  ArrowRightIcon,
  AcademicCapIcon
} from '@heroicons/react/24/outline';
import { useNavigate } from 'react-router-dom';

const Passport = () => {
  const [userInfo, setUserInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authChecked, setAuthChecked] = useState(false);
  const [authorized, setAuthorized] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const verifyAccess = async () => {
      try {
        const response = await fetch('/api/session', {
          credentials: 'include'
        });

        if (response.ok) {
          const data = await response.json();
          if (data.role === 'admin') {
            setAuthorized(true);
          } else {
            navigate('/dashboard', { replace: true });
          }
        } else {
          navigate('/dashboard', { replace: true });
        }
      } catch (error) {
        console.error('Failed to verify access to Passport:', error);
        navigate('/dashboard', { replace: true });
      } finally {
        setAuthChecked(true);
      }
    };

    verifyAccess();
  }, [navigate]);

  useEffect(() => {
    if (authorized) {
      loadUserInfo();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authorized]);

  const loadUserInfo = async () => {
    try {
      // Get Passport info using existing Futures Pulse session
      const response = await fetch('/api/passport/info', {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setUserInfo(data);
      } else {
        console.error('Failed to load passport info');
      }
    } catch (error) {
      console.error('Failed to load passport data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!authChecked || loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-8">
        <div className="text-white text-xl">Loading Passport...</div>
      </div>
    );
  }

  if (!authorized) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-pink-500/5 rounded-full blur-3xl animate-pulse delay-500"></div>
      </div>

      {/* Header */}
      <div className="relative bg-gradient-to-r from-blue-600/90 via-purple-600/90 to-pink-600/90 backdrop-blur-sm border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center backdrop-blur-sm">
              <AcademicCapIcon className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-5xl font-bold text-white tracking-tight">
                Futures Pulse Passport
              </h1>
              <p className="text-white/80 text-xl font-medium">
                Discipleship & Leadership Tracking
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="relative max-w-7xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Push Queue */}
          <div className="lg:col-span-2 bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10">
            <h2 className="text-2xl font-bold text-white mb-4">Push Queue</h2>
            <p className="text-slate-400 mb-4">People ready to move to the next track stop</p>
            <div className="space-y-3">
              <div className="bg-slate-800/50 p-4 rounded-lg">
                <p className="text-white">No candidates ready yet</p>
                <p className="text-sm text-slate-400 mt-1">Complete assignments to see people in the push queue</p>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10">
            <h2 className="text-2xl font-bold text-white mb-4">Quick Actions</h2>
            <div className="space-y-3">
              <button className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 px-4 rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all">
                View Inbox
              </button>
              <button className="w-full bg-slate-700/50 text-white py-3 px-4 rounded-lg hover:bg-slate-700 transition-all">
                View People
              </button>
              <button className="w-full bg-slate-700/50 text-white py-3 px-4 rounded-lg hover:bg-slate-700 transition-all">
                View Reports
              </button>
            </div>
          </div>
        </div>

        {/* Info Notice */}
        <div className="mt-8 bg-blue-500/10 border border-blue-500/30 rounded-2xl p-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 bg-blue-500/20 rounded-xl flex items-center justify-center flex-shrink-0">
              <AcademicCapIcon className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white mb-2">Futures Pulse Passport</h3>
              <p className="text-slate-300 mb-4">
                You're already logged in to Futures Pulse! This Passport system uses your existing session.
              </p>
              <p className="text-slate-300 mb-2">
                <strong>Features:</strong>
              </p>
              <ul className="list-disc list-inside text-slate-300 space-y-2 mb-4 ml-4">
                <li>Track discipleship progression like a passport</li>
                <li>Assign mentors and award digital stamps</li>
                <li>Push people through track stops</li>
                <li>View mentor capacity and assignments</li>
              </ul>
              {userInfo && (
                <div className="bg-slate-800/50 rounded-lg p-4 mt-4">
                  <p className="text-slate-300 text-sm mb-2">
                    <strong>Logged in as:</strong> {userInfo.user?.full_name || userInfo.user?.username} ({userInfo.user?.role})
                  </p>
                  <p className="text-slate-400 text-sm">
                    <strong>Status:</strong> {userInfo.backend_status} | Frontend: {userInfo.frontend_status}
                  </p>
                </div>
              )}
              <div className="bg-slate-800/50 rounded-lg p-4 mt-4">
                <p className="text-slate-400 text-sm">
                  <strong>Note:</strong> Passport backend is ready. Full integration with Futures Pulse auth in progress...
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Passport;

