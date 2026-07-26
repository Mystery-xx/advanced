import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './hooks/useAuth';
import { AppLayout } from './components/AppLayout';
import { ProtectedRoute, AdminRoute } from './components/ProtectedRoute';

import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import UsersPage from './pages/UsersPage';
import OrdersPage from './pages/OrdersPage';
import WeatherPage from './pages/WeatherPage';
import AdminPage from './pages/AdminPage';

function AuthenticatedLayout({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute>
      <AppLayout>{children}</AppLayout>
    </ProtectedRoute>
  );
}

function HomeRedirect() {
  return <Navigate to="/users" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          <Route
            path="/"
            element={
              <AuthenticatedLayout>
                <HomeRedirect />
              </AuthenticatedLayout>
            }
          />
          <Route
            path="/users"
            element={
              <AuthenticatedLayout>
                <UsersPage />
              </AuthenticatedLayout>
            }
          />
          <Route
            path="/orders"
            element={
              <AuthenticatedLayout>
                <OrdersPage />
              </AuthenticatedLayout>
            }
          />
          <Route
            path="/weather"
            element={
              <AuthenticatedLayout>
                <WeatherPage />
              </AuthenticatedLayout>
            }
          />
          <Route
            path="/admin"
            element={
              <AdminRoute>
                <AppLayout>
                  <AdminPage />
                </AppLayout>
              </AdminRoute>
            }
          />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
