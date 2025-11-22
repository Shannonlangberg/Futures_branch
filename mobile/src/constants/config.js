// API Configuration
// In production, this would come from environment variables
// For testing on physical device or simulator, update this to your local IP address
// e.g., 'http://192.168.1.100:5000' (get your IP with: ipconfig getifaddr en0 or ifconfig)
// API Configuration
// In production, this would come from environment variables
// For testing on physical device or simulator, update this to your local IP address
// e.g., 'http://192.168.1.100:5000' (get your IP with: ipconfig getifaddr en0 or ifconfig)
// Production Railway URL
export const API_BASE_URL = 'https://futuresbranch-production.up.railway.app';

// Original config (restore after testing):
// export const API_BASE_URL = __DEV__ 
//   ? 'http://192.168.15.167:5002'  // Your local IP for physical device testing (port 5002, not 5000 - AirPlay uses 5000)
//   : 'https://futures-pulse-production.up.railway.app';

export const STRIPE_PUBLISHABLE_KEY = 'pk_test_51SVOK61uLgcfkEmJo3nyVnfVhKu1kchnuhtkcmsAyfAEXHEKV8KbQtNdqyu5Q3UIFWXpyr0lpNE94aVYdzEOyDXZ00TQfprQ3N';

// App Configuration
export const APP_NAME = 'Futures';
export const APP_TAGLINE = 'One place for church life, discipleship, connection, and growth.';

// Beacon Configuration
export const BEACON_UUID = '00000000-0000-0000-0000-000000000000'; // Replace with your actual beacon UUID

// Colors matching Pulse design
export const Colors = {
  background: '#0f172a',
  surface: '#1e293b',
  surfaceLight: '#334155',
  border: '#475569',
  text: '#ffffff',
  textSecondary: '#cbd5e1',
  textMuted: '#94a3b8',
  primary: '#6366f1',
  primaryDark: '#4f46e5',
  accent: '#8b5cf6',
  success: '#10b981',
  warning: '#f59e0b',
  error: '#ef4444',
  gradientStart: '#6366f1',
  gradientEnd: '#8b5cf6',
};

// Spacing - Updated to match Liven's generous spacing
export const Spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
  // Additional spacing for better hierarchy
  screenPadding: 24, // More generous screen padding
  cardPadding: 20, // More generous card padding
  sectionSpacing: 40, // More space between major sections
  cardGap: 16, // Gap between cards in grids
};

// Font Sizes
export const FontSizes = {
  xs: 12,
  sm: 14,
  md: 16,
  lg: 18,
  xl: 20,
  xxl: 24,
  xxxl: 32,
};

