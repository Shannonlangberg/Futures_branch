import { ApiService } from './ApiService';

export const AuthService = {
  async login(email, password) {
    try {
      console.log('🔐 Attempting login for:', email);
      const response = await ApiService.login(email, password);
      console.log('🔐 Login response:', response);
      
      if (response.authenticated) {
        // Normalize payload
        const userData = response.user ? { ...response.user } : {
          email: response.email || email,
          name: response.name || email.split('@')[0],
          role: response.role,
          campus: response.campus,
        };
        
        // Ensure person_id exists, fetch if missing
        if (userData.person_id) {
          console.log('✅ Login: person_id stored:', userData.person_id);
        } else {
          console.warn('⚠️ Login: No person_id in response, looking up profile for', userData.email);
          try {
            const profileResponse = await ApiService.getPersonProfile(userData.email || email);
            const profile = profileResponse?.profile || profileResponse;
            if (profile?.id) {
              userData.person_id = profile.id;
              console.log('✅ Retrieved person_id via profile lookup:', userData.person_id);
            } else {
              console.warn('⚠️ Profile lookup did not return person_id for', userData.email);
            }
          } catch (profileError) {
            console.error('❌ Failed to fetch person profile for person_id:', profileError);
          }
        }
        
        return {
          success: true,
          token: response.token || 'mock-token', // Backend should return JWT token
          user: userData,
        };
      } else {
        return {
          success: false,
          error: response.error || 'Invalid email or password',
        };
      }
    } catch (error) {
      console.error('❌ Login error:', error);
      
      // Better error messages for different error types
      if (error.code === 'ECONNABORTED') {
        return {
          success: false,
          error: 'Connection timeout. Please check your network connection and ensure you\'re on the same WiFi as your computer.',
        };
      } else if (error.code === 'ECONNREFUSED' || error.code === 'ENETUNREACH') {
        return {
          success: false,
          error: 'Cannot reach server. Please ensure:\n1. Backend is running\n2. You\'re on the same WiFi network\n3. Office network allows device-to-device communication',
        };
      } else if (error.response) {
        // Server responded with an error
        return {
          success: false,
          error: error.response.data?.error || `Server error: ${error.response.status}`,
        };
      } else if (error.request) {
        // Request was made but no response received
        return {
          success: false,
          error: 'No response from server. Check network connection and backend status.',
        };
      } else {
        return {
          success: false,
          error: error.message || 'Login failed',
        };
      }
    }
  },

  async verifyToken(token) {
    try {
      const response = await ApiService.getSession();
      return response.authenticated === true;
    } catch (error) {
      return false;
    }
  },

  async logout() {
    try {
      await ApiService.logout();
      return { success: true };
    } catch (error) {
      console.error('Logout error:', error);
      return { success: false, error: error.message };
    }
  },
};


