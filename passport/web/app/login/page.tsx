'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [leaderId, setLeaderId] = useState('');
  const [email, setEmail] = useState('dev@test.com');
  const [role, setRole] = useState('mentor');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const result = await api.auth.devLogin(leaderId, email, role);
      localStorage.setItem('token', result.token);
      localStorage.setItem('dev_user', `${leaderId}|${email}|${role}`);
      router.push('/leader/home');
    } catch (error: any) {
      alert(`Login failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(to bottom right, #0f172a, #1e293b, #0f172a)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '1rem',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Animated Background */}
      <div style={{
        position: 'fixed',
        inset: 0,
        overflow: 'hidden',
        pointerEvents: 'none',
        zIndex: 0
      }}>
        <div style={{
          position: 'absolute',
          top: '-10rem',
          right: '-10rem',
          width: '20rem',
          height: '20rem',
          background: 'rgba(59, 130, 246, 0.1)',
          borderRadius: '50%',
          filter: 'blur(80px)',
          animation: 'pulse 4s ease-in-out infinite'
        }}></div>
        <div style={{
          position: 'absolute',
          bottom: '-10rem',
          left: '-10rem',
          width: '20rem',
          height: '20rem',
          background: 'rgba(168, 85, 247, 0.1)',
          borderRadius: '50%',
          filter: 'blur(80px)',
          animation: 'pulse 4s ease-in-out infinite 1s'
        }}></div>
      </div>

      <style dangerouslySetInnerHTML={{__html: `
        @keyframes pulse {
          0%, 100% { opacity: 0.5; transform: scale(1); }
          50% { opacity: 0.8; transform: scale(1.1); }
        }
      `}} />

      <div style={{
        width: '100%',
        maxWidth: '28rem',
        position: 'relative',
        zIndex: 1
      }}>
        {/* Logo/Brand */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h1 style={{
            fontSize: '2.5rem',
            fontWeight: 'bold',
            color: 'white',
            marginBottom: '0.5rem'
          }}>Futures Pulse Passport</h1>
          <p style={{ color: '#94a3b8', fontSize: '1.125rem' }}>Discipleship & Leadership Platform</p>
        </div>

        {/* Login Form */}
        <div style={{
          background: 'rgba(30, 41, 59, 0.5)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(71, 85, 105, 0.5)',
          borderRadius: '1.5rem',
          padding: '2rem',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
        }}>
          <div style={{ marginBottom: '1.5rem' }}>
            <h2 style={{
              fontSize: '1.5rem',
              fontWeight: 'bold',
              color: 'white',
              marginBottom: '0.5rem'
            }}>Welcome Back</h2>
            <p style={{ color: '#94a3b8' }}>Sign in to access your dashboard</p>
          </div>

          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div>
              <label style={{
                display: 'block',
                fontSize: '0.875rem',
                fontWeight: '500',
                color: '#cbd5e1',
                marginBottom: '0.75rem'
              }}>
                Leader ID
              </label>
              <input
                type="text"
                value={leaderId}
                onChange={(e) => setLeaderId(e.target.value)}
                required
                style={{
                  width: '100%',
                  padding: '1rem',
                  border: '1px solid #475569',
                  borderRadius: '0.75rem',
                  background: 'rgba(51, 65, 85, 0.5)',
                  color: 'white',
                  fontSize: '1rem',
                  outline: 'none',
                  transition: 'all 0.2s'
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = '#3b82f6';
                  e.target.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)';
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = '#475569';
                  e.target.style.boxShadow = 'none';
                }}
                placeholder="Enter leader ID"
              />
            </div>

            <div>
              <label style={{
                display: 'block',
                fontSize: '0.875rem',
                fontWeight: '500',
                color: '#cbd5e1',
                marginBottom: '0.75rem'
              }}>
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                style={{
                  width: '100%',
                  padding: '1rem',
                  border: '1px solid #475569',
                  borderRadius: '0.75rem',
                  background: 'rgba(51, 65, 85, 0.5)',
                  color: 'white',
                  fontSize: '1rem',
                  outline: 'none',
                  transition: 'all 0.2s'
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = '#3b82f6';
                  e.target.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)';
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = '#475569';
                  e.target.style.boxShadow = 'none';
                }}
                placeholder="dev@test.com"
              />
            </div>

            <div>
              <label style={{
                display: 'block',
                fontSize: '0.875rem',
                fontWeight: '500',
                color: '#cbd5e1',
                marginBottom: '0.75rem'
              }}>
                Role
              </label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                style={{
                  width: '100%',
                  padding: '1rem',
                  border: '1px solid #475569',
                  borderRadius: '0.75rem',
                  background: 'rgba(51, 65, 85, 0.5)',
                  color: 'white',
                  fontSize: '1rem',
                  outline: 'none',
                  transition: 'all 0.2s'
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = '#3b82f6';
                  e.target.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)';
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = '#475569';
                  e.target.style.boxShadow = 'none';
                }}
              >
                <option value="mentor" style={{ background: '#1e293b', color: 'white' }}>Mentor</option>
                <option value="track_owner" style={{ background: '#1e293b', color: 'white' }}>Track Owner</option>
                <option value="campus_pastor" style={{ background: '#1e293b', color: 'white' }}>Campus Pastor</option>
                <option value="admin" style={{ background: '#1e293b', color: 'white' }}>Admin</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                width: '100%',
                padding: '1rem',
                borderRadius: '0.75rem',
                background: loading ? 'rgba(59, 130, 246, 0.5)' : 'linear-gradient(to right, #2563eb, #9333ea)',
                color: 'white',
                fontSize: '1rem',
                fontWeight: '600',
                border: 'none',
                cursor: loading ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s',
                boxShadow: '0 10px 15px -3px rgba(59, 130, 246, 0.25)',
                opacity: loading ? 0.5 : 1
              }}
              onMouseEnter={(e) => {
                if (!loading) {
                  e.currentTarget.style.background = 'linear-gradient(to right, #1d4ed8, #7e22ce)';
                  e.currentTarget.style.boxShadow = '0 20px 25px -5px rgba(59, 130, 246, 0.3)';
                }
              }}
              onMouseLeave={(e) => {
                if (!loading) {
                  e.currentTarget.style.background = 'linear-gradient(to right, #2563eb, #9333ea)';
                  e.currentTarget.style.boxShadow = '0 10px 15px -3px rgba(59, 130, 246, 0.25)';
                }
              }}
            >
              {loading ? 'Logging in...' : 'Login (Dev Mode)'}
            </button>
          </form>
        </div>

        {/* Footer */}
        <div style={{ textAlign: 'center', marginTop: '2rem' }}>
          <p style={{ fontSize: '0.75rem', color: '#64748b' }}>
            © 2025 Futures Church. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  );
}
