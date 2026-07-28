import axios from 'axios';
import type { AuthResponse, LoginRequest, RegisterRequest, User, Order, CreateOrderRequest, WeatherData, PaginatedResponse } from '../types';
import { API_CONFIG, ENDPOINTS } from '../config';

const api = axios.create({
  baseURL: API_CONFIG.baseURL,
  timeout: API_CONFIG.timeout,
  headers: API_CONFIG.headers,
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

export const login = (data: LoginRequest) =>
  api.post<AuthResponse>(ENDPOINTS.AUTH.LOGIN, data).then((r) => r.data);

export const register = (data: RegisterRequest) =>
  api.post<AuthResponse>(ENDPOINTS.AUTH.REGISTER, data).then((r) => r.data);

export const getCurrentUser = () =>
  api.get<User>(ENDPOINTS.AUTH.ME).then((r) => r.data);

export const getUsers = (page = 0, size = 10) =>
  api.get<PaginatedResponse<User>>(ENDPOINTS.USERS.BASE, { params: { page, size } }).then((r) => r.data);

export const getUser = (id: string) =>
  api.get<User>(ENDPOINTS.USERS.BY_ID(id)).then((r) => r.data);

export const createUser = (data: { name: string; email: string; password: string; role?: string }) =>
  api.post<User>(ENDPOINTS.USERS.BASE, data).then((r) => r.data);

export const updateUser = (id: string, data: Partial<User>) =>
  api.put<User>(ENDPOINTS.USERS.BY_ID(id), data).then((r) => r.data);

export const deleteUser = (id: string) =>
  api.delete(ENDPOINTS.USERS.BY_ID(id)).then((r) => r.data);

export const blockUser = (id: string) =>
  api.post<User>(ENDPOINTS.USERS.BLOCK(id)).then((r) => r.data);

export const unblockUser = (id: string) =>
  api.post<User>(ENDPOINTS.USERS.UNBLOCK(id)).then((r) => r.data);

export const getOrders = (page = 0, size = 10) =>
  api.get<PaginatedResponse<Order>>(ENDPOINTS.ORDERS.BASE, { params: { page, size } }).then((r) => r.data);

export const getOrder = (id: string) =>
  api.get<Order>(ENDPOINTS.ORDERS.BY_ID(id)).then((r) => r.data);

export const createOrder = (data: CreateOrderRequest) =>
  api.post<Order>(ENDPOINTS.ORDERS.BASE, data).then((r) => r.data);

export const updateOrderStatus = (id: string, status: Order['status']) =>
  api.patch<Order>(ENDPOINTS.ORDERS.STATUS(id), { status }).then((r) => r.data);

export const getWeather = (city: string) =>
  api.get<WeatherData>(ENDPOINTS.WEATHER.BASE, { params: { city } }).then((r) => r.data);

export const getWeatherHistory = () =>
  api.get<WeatherData[]>(ENDPOINTS.WEATHER.HISTORY).then((r) => r.data);

export const searchUsers = (query: string, page = 0, size = 10) =>
  api.get<PaginatedResponse<User>>(ENDPOINTS.ADMIN.USERS_SEARCH, { params: { query, page, size } }).then((r) => r.data);

export const filterUsersByRole = (role: string, page = 0, size = 10) =>
  api.get<PaginatedResponse<User>>(ENDPOINTS.ADMIN.USERS, { params: { role, page, size } }).then((r) => r.data);

export const adminBlockUser = (id: string) =>
  api.post<User>(ENDPOINTS.ADMIN.BLOCK(id)).then((r) => r.data);

export const adminUnblockUser = (id: string) =>
  api.post<User>(ENDPOINTS.ADMIN.UNBLOCK(id)).then((r) => r.data);

export default api;