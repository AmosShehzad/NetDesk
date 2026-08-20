import { useState } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { Wifi, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [regNumber, setRegNumber] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (user) {
    return <Navigate to={user.role === 'CUSTOMER' ? '/' : '/staff'} replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const profile = await login(regNumber.trim(), password);
      navigate(profile?.role === 'CUSTOMER' ? '/' : '/staff', { replace: true });
    } catch (err) {
      setError(
        err?.response?.data?.detail ||
        'Invalid registration number or password.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="flex items-center gap-3 mb-4" style={{ marginBottom: 24 }}>
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: 12,
              background: 'var(--brand-600)',
              color: '#fff',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Wifi size={22} />
          </div>
          <div>
            <div className="auth-title" style={{ margin: 0, fontSize: 22 }}>NetDesk</div>
            <div className="text-muted text-sm">ISP support, online.</div>
          </div>
        </div>

        <div style={{ fontSize: 18, fontWeight: 600, marginBottom: 4 }}>Sign in</div>
        <div className="text-muted text-sm" style={{ marginBottom: 24 }}>
          Enter your registration number and password.
        </div>

        {error && (
          <div
            className="mb-4"
            style={{
              padding: '10px 14px',
              background: 'rgba(239,68,68,0.1)',
              border: '1px solid rgba(239,68,68,0.25)',
              color: 'var(--danger)',
              borderRadius: 'var(--radius-sm)',
              fontSize: 13,
              marginBottom: 16,
            }}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Registration number</label>
            <input
              type="text"
              value={regNumber}
              onChange={(e) => setRegNumber(e.target.value)}
              placeholder="CUST-2026-00001"
              autoComplete="username"
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="********"
              autoComplete="current-password"
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', marginTop: 8, padding: '10px 16px' }}
            disabled={loading}
          >
            {loading ? (
              <>
                <Loader2 size={16} className="spin" /> Signing in...
              </>
            ) : (
              'Sign in'
            )}
          </button>
        </form>

        <div className="text-xs text-muted" style={{ marginTop: 24, textAlign: 'center' }}>
          Trouble signing in? Contact your ISP support.
        </div>
      </div>
    </div>
  );
}