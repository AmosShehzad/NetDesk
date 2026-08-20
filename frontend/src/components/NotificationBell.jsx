import { useState, useEffect, useRef } from 'react';
import { Bell, CheckCheck } from 'lucide-react';
import client from '../api/client';

function timeAgo(iso) {
  const s = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return 'just now';
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [cleared, setCleared] = useState(false);
  const wrapRef = useRef(null);

  const unread = items.filter((n) => !n.is_read).length;

  const load = async () => {
    setLoading(true);
    try {
      const res = await client.get('/notifications/?page_size=10');
      const data = res.data.results || res.data;
      setItems(data);
      if (data.length > 0) setCleared(false);
    } catch (e) {
      // silent
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const iv = setInterval(load, 30000);
    return () => clearInterval(iv);
  }, []);

  useEffect(() => {
    const onClick = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, []);

  const markAllRead = async () => {
    try {
      await client.patch('/notifications/mark_all_read/');
      setItems([]);
      setCleared(true);
    } catch (e) {
      // silent
    }
  };

  return (
    <div ref={wrapRef} style={{ position: 'relative' }}>
      <button
        className="icon-btn"
        onClick={() => setOpen((o) => !o)}
        aria-label="Notifications"
      >
        <Bell size={20} />
        {unread > 0 && (
          <span
            style={{
              position: 'absolute',
              top: 6,
              right: 6,
              minWidth: 18,
              height: 18,
              padding: '0 5px',
              borderRadius: 9,
              background: 'var(--danger)',
              color: '#fff',
              fontSize: 11,
              fontWeight: 600,
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              lineHeight: 1,
            }}
          >
            {unread > 9 ? '9+' : unread}
          </span>
        )}
      </button>

      {open && (
        <div className="dropdown">
          <div className="dropdown-header flex items-center justify-between">
            <span>Notifications</span>
            {unread > 0 && (
              <button
                className="btn btn-ghost btn-sm"
                onClick={markAllRead}
                style={{ padding: '2px 8px' }}
              >
                <CheckCheck size={14} /> Mark all
              </button>
            )}
          </div>
          <div className="dropdown-body">
            {loading && items.length === 0 && !cleared && (
              <div className="dropdown-item text-muted text-sm">Loading…</div>
            )}
            {!loading && items.length === 0 && (
              <div
                className="dropdown-item text-muted text-sm"
                style={{ textAlign: 'center', padding: '32px 16px' }}
              >
                {cleared ? '✓ All caught up' : "You're all caught up."}
              </div>
            )}
            {items.map((n) => (
              <div
                key={n.id}
                className="dropdown-item"
                style={{
                  background: n.is_read ? 'transparent' : 'rgba(99,102,241,0.05)',
                }}
              >
                <div className="font-medium text-sm">{n.title || n.message}</div>
                {n.title && n.message && (
                  <div className="text-muted text-xs" style={{ marginTop: 4 }}>
                    {n.message}
                  </div>
                )}
                <div
                  className="text-xs"
                  style={{ marginTop: 4, color: 'var(--text-subtle)' }}
                >
                  {timeAgo(n.created_at)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}