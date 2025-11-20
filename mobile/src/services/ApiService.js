import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE_URL } from '../constants/config';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // Increased to 60 seconds for office networks
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Cache-Control': 'no-cache',
  },
  // Add keepalive for better connection handling
  maxRedirects: 5,
  validateStatus: function (status) {
    return status >= 200 && status < 500; // Don't throw on 4xx errors
  },
});

// Add request logging for debugging
api.interceptors.request.use(
  (config) => {
    console.log(`🌐 API Request: ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`);
    return config;
  },
  (error) => {
    console.error('❌ API Request Error:', error);
    return Promise.reject(error);
  }
);

// Add response logging for debugging
api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.config.method?.toUpperCase()} ${response.config.url} - ${response.status}`);
    return response;
  },
  (error) => {
    if (error.code === 'ECONNABORTED') {
      console.error(`⏱️ API Timeout: ${error.config?.method?.toUpperCase()} ${error.config?.url}`);
      console.error(`   Attempted URL: ${error.config?.baseURL}${error.config?.url}`);
    } else if (error.response) {
      console.error(`❌ API Error: ${error.response.status} - ${error.config?.url}`);
    } else if (error.request) {
      console.error(`🌐 Network Error: No response received from ${error.config?.baseURL}${error.config?.url}`);
      console.error(`   This usually means: network unreachable, firewall blocking, or wrong IP address`);
    } else {
      console.error('❌ API Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// Add auth token to requests (separate from logging interceptor)
api.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle auth errors (chained after response logging)
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      await AsyncStorage.removeItem('authToken');
      await AsyncStorage.removeItem('userData');
      // Navigate to login (handled in App.js)
    }
    return Promise.reject(error);
  }
);

export const ApiService = {
  // Auth
  async login(email, password) {
    console.log('📤 Sending login request to:', `${API_BASE_URL}/api/login`);
    console.log('📤 Login data:', { email: email, password: '***' });
    const response = await api.post('/api/login', { 
      email: email.trim(), 
      password: password.trim() 
    }, {
      headers: {
        'Content-Type': 'application/json',
      }
    });
    console.log('📥 Login response received:', response.status, response.data);
    return response.data;
  },
  
  // Network connectivity test
  async testConnection() {
    try {
      const response = await api.get('/api/session', { timeout: 5000 });
      return { success: true, status: response.status };
    } catch (error) {
      return { 
        success: false, 
        error: error.code || error.message,
        url: `${API_BASE_URL}/api/session`
      };
    }
  },

  async getSession() {
    const response = await api.get('/api/session');
    return response.data;
  },

  async logout() {
    const response = await api.post('/api/logout');
    return response.data;
  },

  // Campuses
  async getCampuses() {
    const response = await api.get('/api/campuses/public');
    return response.data;
  },

  async getCampusDetails(campusId) {
    const response = await api.get(`/api/campuses/${campusId}`);
    return response.data;
  },

  // Services/Times
  async getServiceTimes(campusId) {
    const response = await api.get(`/api/service-times?campus=${campusId}`);
    return response.data;
  },

  // Beacon Check-in
  async detectBeacon(personEmail, beaconData) {
    const response = await api.post('/api/beacons/detect', {
      person_email: personEmail,
      ...beaconData,
    });
    return response.data;
  },

  // Prayer
  async submitPrayerRequest(email, request) {
    const response = await api.post('/api/prayer/requests', {
      email,
      ...request,
    });
    return response.data;
  },

  async submitPraiseReport(email, report) {
    const response = await api.post('/api/prayer/praise', {
      email,
      ...report,
    });
    return response.data;
  },

  // Groups
  async getConnectGroups(campus) {
    const response = await api.get(`/api/connect-groups?campus=${campus}`);
    return response.data;
  },

  async getMyGroups(email) {
    const response = await api.get(`/api/connect-groups/my-groups?email=${email}`);
    return response.data;
  },

  async joinGroup(email, groupId) {
    const response = await api.post('/api/connect-groups/join', {
      email,
      group_id: groupId,
    });
    return response.data;
  },

  async submitGroupAttendance(email, groupId, meetingDate, status) {
    const response = await api.post('/api/connect-groups/attendance', {
      email,
      group_id: groupId,
      meeting_date: meetingDate,
      status, // 'present', 'absent', 'apology'
    });
    return response.data;
  },

  // Events
  async getEvents(campus) {
    const response = await api.get(`/api/events?campus=${campus}`);
    return response.data;
  },

  async rsvpEvent(email, eventId, rsvp) {
    const response = await api.post('/api/events/rsvp', {
      email,
      event_id: eventId,
      rsvp, // 'yes', 'no', 'maybe'
    });
    return response.data;
  },

  // Giving
  async createPaymentIntent(amount, type, campus) {
    const response = await api.post('/api/giving/create-intent', {
      amount,
      type, // 'tithe', 'offering', 'missions', 'event'
      campus,
    });
    return response.data;
  },

  async confirmPayment(paymentIntentId, paymentMethodId) {
    const response = await api.post('/api/giving/confirm-payment', {
      payment_intent_id: paymentIntentId,
      payment_method_id: paymentMethodId,
    });
    return response.data;
  },

  async getGivingHistory(email) {
    const response = await api.get(`/api/giving/history?email=${email}`);
    return response.data;
  },

  // Pathways/Passport
  async getMyPathway(email) {
    const response = await api.get(`/api/pathways/my-pathway?email=${email}`);
    return response.data;
  },

  async completePathwayStep(progressId, stepId) {
    const response = await api.post(`/api/pathways/progress/${progressId}/complete-step`, {
      step_id: stepId,
    });
    return response.data;
  },

  // Profile
  async getPersonProfile(email) {
    try {
      // Try to get person by email through persons endpoint
      const response = await api.get(`/api/persons/email/${email}`);
      return { profile: response.data };
    } catch (error) {
      // Fallback: try alternative endpoint
      try {
        const response = await api.get(`/api/people/profile?email=${email}`);
        return response.data;
      } catch (e) {
        throw error;
      }
    }
  },

  async updateProfile(email, updates) {
    console.log('📤 Updating profile for:', email, updates);
    const response = await api.put('/api/people/profile', { email, ...updates });
    console.log('📥 Profile update response:', response.data);
    return response.data;
  },

  // Push Notifications
  async savePushToken(email, pushToken) {
    const response = await api.post('/api/push-tokens', {
      email,
      push_token: pushToken,
    });
    return response.data;
  },

  // Attendance Logging (for "I'm Here" button - adds to heartbeat gather metric)
  async logAttendance(email, attendanceData) {
    try {
      const response = await api.post('/api/attendance/log', {
        email,
        ...attendanceData
      });
      return response.data;
    } catch (error) {
      console.error('Error logging attendance:', error);
      throw error;
    }
  },

  // Engagement Logging (for sermon notes, etc.)
  async logEngagement(email, type, data) {
    try {
      const response = await api.post('/api/engagement/log', {
        email,
        type,
        ...data
      });
      return response.data;
    } catch (error) {
      console.error('Error logging engagement:', error);
      throw error;
    }
  },
};

