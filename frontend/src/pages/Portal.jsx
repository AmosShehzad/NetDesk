import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { CreditCard, Bell, MessageSquarePlus, Inbox } from 'lucide-react';
import client from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function Portal() {
  const { user } = useAuth();
  const [bills, setBills] = useState([]);
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    client.get('/bills/').then((res) => setBills(res.data.results || res.data));
    client.get('/notifications/').then((res) => setNotifications(res.data.results || res.data));
  }, []);

  const latestBill = bills[0];

  const timeAgo = (dateStr) => {
    const diff = Math.floor((Date.now() - new Date(dateStr)) / 1000);
    if (diff < 60) return 'just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div className="portal-header">
        <h2>Welcome back, {user?.username || user?.reg_number}</h2>
        <p>Here's what's happening with your account.</p>
      </div>

      <div className="card card-pad">
        <div className="section-title"><CreditCard size={16} /> Current bill</div>
        {latestBill ? (
          <div className="bill-row">
            <div>
              <div className="bill-amount">Rs. {latestBill.amount}</div>
              <div className="bill-month">{latestBill.month} · Due {latestBill.due_date}</div>
            </div>
            <span className={`pill ${latestBill.status === 'PAID' ? 'pill-paid' : 'pill-unpaid'}`}>
              {latestBill.status}
            </span>
          </div>
        ) : (
          <div className="empty-state" style={{ padding: 20 }}>
            <Inbox size={24} color="var(--gray-300)" style={{ marginBottom: 6 }} />
            <p style={{ margin: 0 }}>No bills yet.</p>
          </div>
        )}
      </div>

      <div className="card card-pad">
        <div className="section-title"><Bell size={16} /> Messages from NetDesk</div>
        {notifications.length === 0 ? (
          <div className="empty-state" style={{ padding: 20 }}>
            <Inbox size={24} color="var(--gray-300)" style={{ marginBottom: 6 }} />
            <p style={{ margin: 0 }}>No messages.</p>
          </div>
        ) : (
          notifications.map((n) => (
            <div key={n.id} className="message-item">
              <div className="message-icon"><Bell size={14} /></div>
              <div>
                <div className="message-text">{n.message}</div>
                <div className="message-time">{timeAgo(n.created_at)}</div>
              </div>
            </div>
          ))
        )}
      </div>

      <Link to="/tickets" className="btn btn-primary report-btn" style={{ textDecoration: 'none' }}>
        <MessageSquarePlus size={18} /> Report an issue
      </Link>
    </div>
  );
}