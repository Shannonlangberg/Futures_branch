import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import MainLayout from '../components/MainLayout';

const ViewEmail = () => {
  const { token } = useParams();
  const navigate = useNavigate();
  const [emailContent, setEmailContent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchEmail = async () => {
      try {
        const response = await fetch(`/api/communication/view-email/${token}`, {
          credentials: 'include',
          redirect: 'follow'
        });

        if (response.redirected) {
          // Redirected to login - follow the redirect
          window.location.href = response.url;
          return;
        }

        if (!response.ok) {
          const data = await response.json().catch(() => ({}));
          setError(data.error || 'Failed to load email');
          setLoading(false);
          return;
        }

        const html = await response.text();
        setEmailContent(html);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching email:', err);
        setError('Error loading email. Please try again.');
        setLoading(false);
      }
    };

    if (token) {
      fetchEmail();
    }
  }, [token]);

  if (loading) {
    return (
      <MainLayout>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-white">Loading email...</div>
        </div>
      </MainLayout>
    );
  }

  if (error) {
    return (
      <MainLayout>
        <div className="min-h-screen flex items-center justify-center">
          <div className="bg-red-500/20 border border-red-500/40 rounded-xl p-6 max-w-md">
            <h2 className="text-xl font-bold text-white mb-2">Error</h2>
            <p className="text-white/80">{error}</p>
            <button
              onClick={() => navigate('/')}
              className="mt-4 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg"
            >
              Go to Dashboard
            </button>
          </div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="min-h-screen bg-slate-900 py-8">
        <div className="max-w-4xl mx-auto px-4">
          <div dangerouslySetInnerHTML={{ __html: emailContent }} />
        </div>
      </div>
    </MainLayout>
  );
};

export default ViewEmail;

