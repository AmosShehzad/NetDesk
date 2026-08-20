import { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Ticket,
  KeyRound,
  LogOut,
  Menu,
  Sun,
  Moon,
  X,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import NotificationBell from './NotificationBell';

export default function Layout() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const initials = (user?.username || user?.full_name || '?')
    .split(' ')
    .map((s) => s[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

  return (
    <div className="app-shell">
      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="flex items-center justify-between mb-4">
          <div className="sidebar-logo" style={{ margin: 0, padding: 0 }}>NetDesk</div>
          <button
            className="icon-btn hamburger"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close menu"
          >
            <X size={18} />
          </button>
        </div>

        <nav className="flex flex-col gap-2" style={{ flex: 1 }}>
          <NavLink
            to="/"
            end
            className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
            onClick={() => setSidebarOpen(false)}
          >
            <LayoutDashboard size={18} /> Dashboard
          </NavLink>
          <NavLink
            to="/tickets"
            className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
            onClick={() => setSidebarOpen(false)}
          >
            <Ticket size={18} /> Tickets
          </NavLink>
          <NavLink
            to="/change-password"
            className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
            onClick={() => setSidebarOpen(false)}
          >
            <KeyRound size={18} /> Password
          </NavLink>
        </nav>

        <button className="sidebar-link" onClick={handleLogout} style={{ textAlign: 'left' }}>
          <LogOut size={18} /> Log out
        </button>
      </aside>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          onClick={() => setSidebarOpen(false)}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.4)',
            zIndex: 45,
          }}
        />
      )}

      {/* Main column */}
      <div className="main">
        <header className="topbar">
          <div className="flex items-center gap-3">
            <button
              className="icon-btn hamburger"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open menu"
            >
              <Menu size={20} />
            </button>
            <div className="font-semibold" style={{ fontSize: 15 }}>
              Welcome back{user?.username ? `, ${user.username}` : ''}
            </div>
          </div>

          <div className="topbar-actions">
            <button
              className="icon-btn"
              onClick={toggleTheme}
              aria-label="Toggle theme"
              title={theme === 'light' ? 'Switch to dark' : 'Switch to light'}
            >
              {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
            </button>

            <NotificationBell />

            <div
              className="flex items-center gap-2"
              style={{ paddingLeft: 12, borderLeft: '1px solid var(--border)' }}
            >
              <div
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: '50%',
                  background: 'var(--brand-600)',
                  color: '#fff',
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 600,
                  fontSize: 13,
                }}
              >
                {initials}
              </div>
              <div style={{ lineHeight: 1.2 }}>
                <div className="text-sm font-medium">{user?.username || 'User'}</div>
                <div className="text-xs text-muted">{user?.role || ''}</div>
              </div>
            </div>
          </div>
        </header>

        <main className="page">
          <Outlet />
        </main>
      </div>
    </div>
  );
}