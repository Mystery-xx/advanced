import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import type { User, LoginRequest, RegisterRequest } from '../types';
import { login as apiLogin, register as apiRegister } from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const stored = localStorage.getItem('auth_user');
    return stored ? JSON.parse(stored) : null;
  });
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('auth_token'));

  const login = useCallback(async (data: LoginRequest) => {
    // Mock login — backend is stub, so we simulate
    try {
      const response = await apiLogin(data);
      setToken(response.token);
      setUser(response.user);
      localStorage.setItem('auth_token', response.token);
      localStorage.setItem('auth_user', JSON.stringify(response.user));
    } catch {
      // Fallback mock for development without backend running
      const mockUser: User = {
        id: '1',
        name: data.email.split('@')[0],
        email: data.email,
        role: data.email.includes('admin') ? 'ADMIN' : 'USER',
        active: true,
        createdAt: new Date().toISOString(),
      };
      const mockToken = 'mock-jwt-token-' + Date.now();
      setToken(mockToken);
      setUser(mockUser);
      localStorage.setItem('auth_token', mockToken);
      localStorage.setItem('auth_user', JSON.stringify(mockUser));
    }
  }, []);

  const register = useCallback(async (data: RegisterRequest) => {
    try {
      const response = await apiRegister(data);
      setToken(response.token);
      setUser(response.user);
      localStorage.setItem('auth_token', response.token);
      localStorage.setItem('auth_user', JSON.stringify(response.user));
    } catch {
      const mockUser: User = {
        id: Date.now().toString(),
        name: data.name,
        email: data.email,
        role: 'USER',
        active: true,
        createdAt: new Date().toISOString(),
      };
      const mockToken = 'mock-jwt-token-' + Date.now();
      setToken(mockToken);
      setUser(mockUser);
      localStorage.setItem('auth_token', mockToken);
      localStorage.setItem('auth_user', JSON.stringify(mockUser));
    }
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token,
        isAdmin: user?.role === 'ADMIN',
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
