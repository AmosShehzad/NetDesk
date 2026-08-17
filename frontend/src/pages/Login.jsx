import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';

export default function Login() {
  const [reg_number, setRegNumber] = useState('');
  const [password, setPassword] = useState('');
  const { login } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const profile = await login(reg_number, password);
      navigate(profile.must_change_password ? '/change-password' : '/portal');
    } catch (err) {
      showToast(err.response?.data?.detail || 'Login failed. Check your credentials.');
    }
  };

  return (
    <div className="auth-shell">
      <div className="auth-brand">
        <div className="brand" style={{ marginBottom: 40 }}>
          <div className="brand-mark">ND</div>
          <div className="brand-name" style={{ fontSize: 16 }}>NetDesk</div>
        </div>
        <h1>Support, online.</h1>
        <p>Track tickets, talk to your customers, and keep every connection up — from one desk.</p>
        <div className="auth-signal">
          <span></span><span></span><span></span><span></span>
        </div>
      </div>
      <div className="auth-form-side">
        <form className="auth-form" onSubmit={handleSubmit}>
          <h2>Sign in</h2>
          <div className="subtitle">Enter your registration number and password.</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div className="field">
              <label>Registration number</label>
              <input 
                className="input" 
                placeholder="Registration number (e.g. CUST-2026-00001)" 
                value={reg_number} 
                onChange={(e) => setRegNumber(e.target.value)} 
              />
            </div>
            <div className="field">
              <label>Password</label>
              <input 
                className="input" 
                type="password" 
                placeholder="••••••••" 
                value={password} 
                onChange={(e) => setPassword(e.target.value)} 
              />
            </div>
            <button type="submit" className="btn btn-primary btn-block">Sign in</button>
          </div>
        </form>
      </div>
    </div>
  );
}