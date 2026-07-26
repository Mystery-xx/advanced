import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import './Layout.css';

const navItems = [
  { path: '/users', label: 'Users', roles: ['USER', 'ADMIN'] },
  { path: '/orders', label: 'Orders', roles: ['USER', 'ADMIN'] },
  { path: '/weather', label: 'Weather', roles: ['USER', 'ADMIN'] },
  { path: '/admin', label: 'Admin', roles: ['ADMIN'] },
];

export function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, isAdmin, logout } = useAuth();
  const location = useLocation();

  const visibleItems = navItems.filter(
    (item) => item.roles.includes(isAdmin ? 'ADMIN' : 'USER')
  );

  return (
    <div className="app-layout">
      <header className="app-header">
        <div className="header-left">
          <Link to="/" className="logo">
            Test App
          </Link>
          <nav className="main-nav">
            {visibleItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`nav-link ${location.pathname === item.path ? 'active' : ''}`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
        <div className="header-right">
          <span className="user-greeting">
            {user?.name} ({user?.role})
          </span>
          <button onClick={logout} className="btn btn-sm btn-outline">
            Logout
          </button>
        </div>
      </header>
      <main className="app-main">{children}</main>
    </div>
  );
}
