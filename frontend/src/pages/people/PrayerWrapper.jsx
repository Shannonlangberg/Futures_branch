import React from 'react';
import PastoralCare from './PastoralCare';
import { useSearchParams } from 'react-router-dom';

/**
 * Wrapper component that renders Pastoral Care page with prayer tab active.
 * This ensures /prayer shows the full-featured prayer management integrated with Heartbeat.
 */
const PrayerWrapper = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  
  // Ensure the tab is set to 'prayer' if not already set
  React.useEffect(() => {
    if (searchParams.get('tab') !== 'prayer') {
      setSearchParams({ tab: 'prayer' });
    }
  }, [searchParams, setSearchParams]);
  
  // Render PastoralCare directly - it will read the tab parameter
  return <PastoralCare />;
};

export default PrayerWrapper;

