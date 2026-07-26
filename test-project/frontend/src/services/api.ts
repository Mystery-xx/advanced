import axios from 'axios';
import type { AuthResponse, LoginRequest, RegisterRequest, User, Order, CreateOrderRequest, WeatherData, PaginatedResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth
export const login = (data: LoginRequest) =>
  api.post<AuthResponse>('/auth/login', data).then((r) => r.data);

export const register = (data: RegisterRequest) =>
  api.post<AuthResponse>('/auth/register', data).then((r) => r.data);

export const getCurrentUser = () =>
  api.get<User>('/auth/me').then((r) => r.data);

// Users
export const getUsers = (page = 0, size = 10) =>
  api.get<PaginatedResponse<User>>('/users', { params: { page, size } }).then((r) => r.data);

export const getUser = (id: string) =>
  api.get<User>(`/users/${id}`).then((r) => r.data);

export const createUser = (data: { name: string; email: string; password: string; role?: string }) =>
  api.post<User>('/users', data).then((r) => r.data);

export const updateUser = (id: string, data: Partial<User>) =>
  api.put<User>(`/users/${id}`, data).then((r) => r.data);

export const deleteUser = (id: string) =>
  api.delete(`/users/${id}`).then((r) => r.data);

export const blockUser = (id: string) =>
  api.post<User>(`/users/${id}/block`).then((r) => r.data);

export const unblockUser = (id: string) =>
  api.post<User>(`/users/${id}/unblock`).then((r) => r.data);

// Orders
export const getOrders = (page = 0, size = 10) =>
  api.get<PaginatedResponse<Order>>('/orders', { params: { page, size } }).then((r) => r.data);

export const getOrder = (id: string) =>
  api.get<Order>(`/orders/${id}`).then((r) => r.data);

export const createOrder = (data: CreateOrderRequest) =>
  api.post<Order>('/orders', data).then((r) => r.data);

export const updateOrderStatus = (id: string, status: Order['status']) =>
  api.patch<Order>(`/orders/${id}/status`, { status }).then((r) => r.data);

// Weather
export const getWeather = (city: string) =>
  api.get<WeatherData>('/weather', { params: { city } }).then((r) => r.data);

export const getWeatherHistory = () =>
  api.get<WeatherData[]>('/weather/history').then((r) => r.data);

// Admin
export const searchUsers = (query: string, page = 0, size = 10) =>
  api.get<PaginatedResponse<User>>('/admin/users/search', { params: { query, page, size } }).then((r) => r.data);

export const filterUsersByRole = (role: string, page = 0, size = 10) =>
  api.get<PaginatedResponse<User>>('/admin/users', { params: { role, page, size } }).then((r) => r.data);

export const adminBlockUser = (id: string) =>
  api.post<User>(`/admin/users/${id}/block`).then((r) => r.data);

export const adminUnblockUser = (id: string) =>
  api.post<User>(`/admin/users/${id}/unblock`).then((r) => r.data);

export default api;
