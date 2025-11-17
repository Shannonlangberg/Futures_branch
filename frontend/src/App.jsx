import React, { useState, useEffect } from 'react';
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
import ConnectGroups from './pages/ConnectGroups';
import ConnectGroupLeader from './pages/ConnectGroupLeader';
import People from './pages/People';
import Passport from './pages/Passport';
import PersonHealthReport from './pages/PersonHealthReport';
import Landing from './pages/Landing';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const response = await fetch('/api/session', {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setIsAuthenticated(data.authenticated);
      } else {
        setIsAuthenticated(false);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogin = () => {
    setIsAuthenticated(true);
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
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <Router>
      <Routes>
        <Route 
          path="/login" 
          element={
            isAuthenticated ? 
            <Navigate to="/dashboard" replace /> : 
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
                  <Route path="/home" element={<Landing />} />
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/stats" element={<LogStats />} />
                  <Route path="/finance" element={<Finance />} />
                  <Route path="/campuses" element={<CampusManagement />} />
                  <Route path="/users" element={<UserManagement />} />
                  <Route path="/export" element={<DataExport />} />
                  <Route path="/profile" element={<MyProfile />} />
                  <Route path="/people" element={<People />} />
                  <Route path="/persons/:id" element={<PersonHealthReport />} />
                  <Route path="/passport" element={<Passport />} />
                  <Route path="/journey" element={<Passport />} />
                  <Route path="/connect-groups" element={<ConnectGroups />} />
                  <Route path="/connect-groups/leader" element={<ConnectGroupLeader />} />
                  <Route path="/settings" element={<Navigate to="/profile" replace />} />
                  <Route path="*" element={<Navigate to="/dashboard" replace />} />
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
