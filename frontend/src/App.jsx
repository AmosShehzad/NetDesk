import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import Layout from './components/Layout';
import Login from './pages/Login';
import Portal from './pages/Portal';
import Tickets from './pages/Tickets';
import TicketDetail from './pages/TicketDetail';
import ChangePassword from './pages/ChangePassword';
import StaffDashboard from './pages/StaffDashboard';
import './styles/global.css';
import AgentQueue from './pages/AgentQueue';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="auth-shell"><div className="text-muted">Loading…</div></div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function StaffRoute({ children }) {
  const { user } = useAuth();
  if (user && user.role === 'CUSTOMER') return <Navigate to="/" replace />;
  return children;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Portal />} />
        <Route path="/tickets" element={<Tickets />} />
        <Route path="/tickets/:id" element={<TicketDetail />} />
        <Route path="/change-password" element={<ChangePassword />} />
        <Route path="/staff" element={<StaffRoute><StaffDashboard /></StaffRoute>} />
        <Route path="/queue" element={<StaffRoute><AgentQueue /></StaffRoute>} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <AuthProvider>
          <ToastProvider>
            <AppRoutes />
          </ToastProvider>
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  );
}