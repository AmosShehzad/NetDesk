import { Link, Outlet, useLocation } from 'react-router-dom';
import { Ticket, User, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Layout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const initials = (user?.username || user?.phone_number || '?').slice(0, 2).toUpperCase();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">ND</div>
          <div className="brand-name">NetDesk</div>
        </div>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <Link to="/portal" className={`nav-link ${location.pathname === '/portal' ? 'active' : ''}`}>
            <User size={16} /> My Account
          </Link>
          <Link to="/tickets" className={`nav-link ${location.pathname.startsWith('/tickets') ? 'active' : ''}`}>
            <Ticket size={16} /> Tickets
          </Link>
        </nav>
      </aside>
      <div style={{ flex: 1 }}>
        <header className="topbar">
          <div className="user-chip">
            <div className="avatar">{initials}</div>
            <div>
              <div style={{ fontWeight: 500 }}>{user?.username || user?.phone_number}</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--gray-500)' }}>{user?.role}</div>
            </div>
          </div>
          <button onClick={logout} className="btn btn-ghost" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <LogOut size={14} /> Log out
          </button>
        </header>
        <main className="main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}