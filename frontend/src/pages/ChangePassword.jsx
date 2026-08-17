import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import client from '../api/client';
import { useToast } from '../context/ToastContext';

export default function ChangePassword() {
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const { showToast } = useToast();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await client.post('/users/change-password/', { old_password: oldPassword, new_password: newPassword });
      navigate('/portal');
    } catch (err) {
      showToast(err.response?.data?.old_password?.[0] || err.response?.data?.old_password || 'Failed to change password.');
    }
  };

  return (
    <div style={{ maxWidth: 360, margin: '80px auto' }} className="card card-pad">
      <h2>Change your password</h2>
      <p className="subtitle">You must set a new password before continuing.</p>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div className="field">
          <label>Current password</label>
          <input className="input" type="password" value={oldPassword} onChange={(e) => setOldPassword(e.target.value)} />
        </div>
        <div className="field">
          <label>New password</label>
          <input className="input" type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
        </div>
        <button className="btn btn-primary">Update password</button>
      </form>
    </div>
  );
}