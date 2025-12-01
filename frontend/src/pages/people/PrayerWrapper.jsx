import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';

/**
 * Wrapper component that redirects to Pastoral Care page with prayer tab active.
 * This ensures /prayer shows the full-featured prayer management integrated with Heartbeat.
 */
const PrayerWrapper = () => {
  const location = useLocation();
  
  // Preserve any query parameters from the original request
  const searchParams = new URLSearchParams(location.search);
  searchParams.set('tab', 'prayer');
  
  return <Navigate to={`/people/pastoral-care?${searchParams.toString()}`} replace />;
};

export default PrayerWrapper;

