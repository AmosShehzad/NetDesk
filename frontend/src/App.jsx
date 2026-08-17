import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import Layout from './components/Layout';
import Login from './pages/Login';
import Portal from './pages/Portal';
import ChangePassword from './pages/ChangePassword';
import Tickets from './pages/Tickets';
import TicketDetail from './pages/TicketDetail';
import './styles/global.css';

function PrivateRoute({ children }) {
  const token = localStorage.getItem('access');
  return token ? children : <Navigate to="/login" />;
}

export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
              <Route index element={<Navigate to="/portal" />} />
              <Route path="portal" element={<Portal />} />
              <Route path="change-password" element={<ChangePassword />} />
              <Route path="tickets" element={<Tickets />} />
              <Route path="tickets/:id" element={<TicketDetail />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ToastProvider>
  );
}