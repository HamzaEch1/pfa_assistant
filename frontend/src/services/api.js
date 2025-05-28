// src/services/api.js
import axios from 'axios';

// Get the API base URL from environment variables (defined in .env)
// Fallback to localhost:8000 for development if not set
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create an Axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 600000, // 10 minutes timeout
  timeoutErrorMessage: 'La requête a pris trop de temps. Veuillez réessayer.',
});

// Interceptor to add the JWT token to requests if available
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken'); // Get token from local storage
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for better error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED') {
      console.error('Request timeout:', error);
      return Promise.reject({
        message: 'La requête a expiré. Veuillez réessayer.',
        originalError: error
      });
    }
    return Promise.reject(error);
  }
);

// --- Authentication Service ---
export const authService = {
  login: (username, password) => {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);
    return apiClient.post('/api/v1/auth/login', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
  },
  verifyTwoFactor: (username, code) => {
    return apiClient.post('/api/v1/auth/verify-2fa', {
      username,
      code
    });
  },
  signup: (userData) => {
    return apiClient.post('/api/v1/auth/signup', userData);
  },
  getCurrentUser: () => {
    return apiClient.get('/api/v1/auth/me');
  },
  setupTwoFactor: () => {
    return apiClient.post('/api/v1/auth/setup-2fa');
  },
  confirmTwoFactor: (code) => {
    return apiClient.post('/api/v1/auth/confirm-2fa', { code });
  },
  disableTwoFactor: () => {
    return apiClient.post('/api/v1/auth/disable-2fa');
  }
};

// --- Chat Service ---
export const chatService = {
  startConversation: () => {
    // This endpoint might not be needed if handled by /message implicitly
    // Keeping it based on previous structure
    return apiClient.post('/api/v1/chat/conversations');
  },
  getConversations: (skip = 0, limit = 100) => {
    return apiClient.get(`/api/v1/chat/conversations?skip=${skip}&limit=${limit}`);
  },
  getConversation: (conversationId) => {
    return apiClient.get(`/api/v1/chat/conversations/${conversationId}`);
  },
  deleteConversation: (conversationId) => {
    return apiClient.delete(`/api/v1/chat/conversations/${conversationId}`);
  },
  sendMessage: (messageData, signal) => {
    return apiClient.post('/api/v1/chat/message', messageData, { signal });
  },
  deleteMessage: (conversationId, messageId) => {
    return apiClient.delete(`/api/v1/chat/conversations/${conversationId}/messages/${messageId}`);
  },
  uploadExcelFile: (conversationId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post(`/api/v1/chat/conversations/${conversationId}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  getFileContext: (fileId) => {
    return apiClient.get(`/api/v1/chat/file-context/${fileId}`);
  },
  // Add function to submit feedback
  submitFeedback: (conversationId, messageIndex, feedbackData) => {
    return apiClient.post(`/api/v1/chat/conversations/${conversationId}/messages/${messageIndex}/feedback`, feedbackData);
  },
  // Add function to get statistics
  getStatistics: () => {
    return apiClient.get('/api/v1/chat/statistics');
  }
};

// --- NEW: Admin Service ---
export const adminService = {
  // Users
  getUsers: (skip = 0, limit = 100) => {
    return apiClient.get(`/api/v1/admin/users?skip=${skip}&limit=${limit}`);
  },
  deleteUser: (username) => {
    return apiClient.delete(`/api/v1/admin/users/${username}`);
  },
  setUserAdminStatus: (username, isAdmin) => {
    return apiClient.put(`/api/v1/admin/users/${username}/admin-status`, { is_admin: isAdmin });
  },
  // Feedback
  getFeedback: () => {
    return apiClient.get('/api/v1/admin/feedback');
  },
  clearFeedback: (conversationId, messageIndex) => {
    return apiClient.delete(`/api/v1/admin/feedback/${conversationId}/${messageIndex}`);
  },
  // Catalog
  getCatalogInfo: () => {
    return apiClient.get('/api/v1/admin/catalog/info');
  },
  uploadCatalogFile: (file) => {
    const formData = new FormData();
    formData.append('file', file); // 'file' must match the parameter name in FastAPI endpoint
    return apiClient.post('/api/v1/admin/catalog/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      // Optional: Add progress tracking here if needed
    });
  },
  // Config
  getAdminConfig: () => {
     return apiClient.get('/api/v1/admin/config');
  },
  updateAdminEmail: (newEmail) => {
     return apiClient.put('/api/v1/admin/config/admin-email', { new_email: newEmail });
  }
  // Add other admin endpoints here...
};

export default apiClient; // Keep default export if needed elsewhere