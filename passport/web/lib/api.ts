const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function apiRequest(
  endpoint: string,
  options: RequestInit = {}
): Promise<any> {
  const token = localStorage.getItem('token');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Dev mode header
  if (process.env.NODE_ENV === 'development') {
    const devUser = localStorage.getItem('dev_user');
    if (devUser) {
      headers['X-Dev-User'] = devUser;
    }
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(error.error || `HTTP ${response.status}`);
  }

  return response.json();
}

export const api = {
  auth: {
    devLogin: (leaderId: string, email: string, role: string) =>
      apiRequest('/api/auth/dev-login', {
        method: 'POST',
        body: JSON.stringify({ leader_id: leaderId, email, role }),
      }),
  },
  leaders: {
    getMe: () => apiRequest('/api/leaders/me'),
  },
  people: {
    getAll: (campusId?: string) =>
      apiRequest(`/api/people${campusId ? `?campus_id=${campusId}` : ''}`),
    getById: (personId: string) => apiRequest(`/api/people/${personId}`),
  },
  inbox: {
    getAll: (status?: string) =>
      apiRequest(`/api/inbox${status ? `?status=${status}` : ''}`),
  },
  pushQueue: {
    getAll: (campusId?: string) =>
      apiRequest(`/api/push-queue${campusId ? `?campus_id=${campusId}` : ''}`),
  },
  push: {
    create: (data: any) =>
      apiRequest('/api/push', { method: 'POST', body: JSON.stringify(data) }),
  },
  transfer: {
    accept: (transferId: string) =>
      apiRequest(`/api/transfer/${transferId}/accept`, { method: 'POST' }),
  },
  complete: {
    complete: (data: any) =>
      apiRequest('/api/complete', { method: 'POST', body: JSON.stringify(data) }),
  },
  stamps: {
    getPending: () => apiRequest('/api/stamps/pending'),
    approve: (stampId: string) =>
      apiRequest(`/api/stamps/${stampId}/approve`, { method: 'POST' }),
  },
  tracks: {
    getAll: (campusId?: string) =>
      apiRequest(`/api/tracks${campusId ? `?campus_id=${campusId}` : ''}`),
    getStops: (trackId: string) => apiRequest(`/api/tracks/${trackId}/stops`),
  },
  reports: {
    trackHealth: (trackId: string) =>
      apiRequest(`/api/reports/track-health?track_id=${trackId}`),
    mentorLoad: (campusId?: string) =>
      apiRequest(`/api/reports/mentor-load${campusId ? `?campus_id=${campusId}` : ''}`),
  },
  notes: {
    create: (data: any) =>
      apiRequest('/api/notes', { method: 'POST', body: JSON.stringify(data) }),
    getByPerson: (personId: string) => apiRequest(`/api/notes/person/${personId}`),
  },
  passport: {
    getByPerson: (personId: string) => apiRequest(`/api/passport/${personId}`),
  },
};





