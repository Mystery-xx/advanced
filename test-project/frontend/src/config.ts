export const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
};

export const ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    ME: '/auth/me',
  },
  USERS: {
    BASE: '/users',
    BY_ID: (id: string) => `/users/${id}`,
    BLOCK: (id: string) => `/users/${id}/block`,
    UNBLOCK: (id: string) => `/users/${id}/unblock`,
  },
  ORDERS: {
    BASE: '/orders',
    BY_ID: (id: string) => `/orders/${id}`,
    STATUS: (id: string) => `/orders/${id}/status`,
  },
  WEATHER: {
    BASE: '/weather',
    HISTORY: '/weather/history',
  },
  ADMIN: {
    USERS_SEARCH: '/admin/users/search',
    USERS: '/admin/users',
    BLOCK: (id: string) => `/admin/users/${id}/block`,
    UNBLOCK: (id: string) => `/admin/users/${id}/unblock`,
  },
} as const;