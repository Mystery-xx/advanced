export interface User {
  id: string;
  name: string;
  email: string;
  role: 'USER' | 'ADMIN';
  active: boolean;
  createdAt: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export interface Order {
  id: string;
  userId: string;
  product: string;
  quantity: number;
  status: 'PENDING' | 'CONFIRMED' | 'SHIPPED' | 'DELIVERED' | 'CANCELLED';
  total: number;
  createdAt: string;
}

export interface CreateOrderRequest {
  product: string;
  quantity: number;
  total: number;
}

export interface WeatherData {
  city: string;
  temperature: number;
  humidity: number;
  windSpeed: number;
  description: string;
  icon: string;
  timestamp: string;
}

export interface AdminAction {
  userId: string;
  action: 'BLOCK' | 'UNBLOCK';
}

export interface PaginatedResponse<T> {
  content: T[];
  totalPages: number;
  totalElements: number;
  currentPage: number;
}
