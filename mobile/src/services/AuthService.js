import { ApiService } from './ApiService';

export const AuthService = {
  async login(email, password) {
    try {
      const response = await ApiService.login(email, password);
      
      if (response.authenticated) {
        return {
          success: true,
          token: response.token || 'mock-token', // Backend should return JWT token
          user: {
            email: response.email || email,
            name: response.name || email.split('@')[0],
            role: response.role,
            campus: response.campus,
          },
        };
      } else {
        return {
          success: false,
          error: response.error || 'Invalid email or password',
        };
      }
    } catch (error) {
      console.error('Login error:', error);
      return {
        success: false,
        error: error.response?.data?.error || error.message || 'Login failed',
      };
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


