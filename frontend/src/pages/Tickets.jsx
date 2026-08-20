import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, X, Loader2, AlertTriangle } from 'lucide-react';
import client from '../api/client';
import { useToast } from '../context/ToastContext';

function StatusBadge({ status }) {
  const map = {
    OPEN:       { cls: 'badge-info',    label: 'Open' },
    ASSIGNED:   { cls: 'badge-brand',   label: 'Assigned' },
    IN_PROGRESS:{ cls: 'badge-warning', label: 'In progress' },
    RESOLVED:   { cls: 'badge-success', label: 'Resolved' },
    CLOSED:     { cls: 'badge-muted',   label: 'Closed' },
    ESCALATED:  { cls: 'badge-danger',  label: 'Escalated' },
  };
  const s = map[status] || { cls: 'badge-muted', label: status };
  return <span className={`badge ${s.cls}`}>{s.label}</span>;
}

function PriorityBadge({ priority }) {
  const map = {
    LOW:      'badge-muted',
    MEDIUM:   'badge-info',
    HIGH:     'badge-warning',
    CRITICAL: 'badge-danger',
  };
  return <span className={`badge ${map[priority] || 'badge-muted'}`}>{priority}</span>;
}

function SlaBadge({ status, hours }) {
  if (status === 'BREACHED')
    return <span className="badge badge-danger">Breached</span>;
  if (status === 'WARNING')
    return <span className="badge badge-warning">{hours}h left</span>;
  if (status === 'RESOLVED')
    return <span className="badge badge-muted">—</span>;
  return <span className="badge badge-success">{hours}h left</span>;
}

export default function Tickets() {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [tickets, setTickets] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('all');
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);

  // New ticket form
  const [form, setForm] = useState({ title: '', description: '', category: '' });
  const [submitting, setSubmitting] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [tRes, cRes] = await Promise.allSettled([
        client.get('/tickets/?page_size=100'),
        client.get('/categories/'),
      ]);
      if (tRes.status === 'fulfilled') {
        setTickets(tRes.value.data.results || tRes.value.data);
      }
      if (cRes.status === 'fulfilled') {
        setCategories(cRes.value.data.results || cRes.value.data);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const filtered = useMemo(() => {
    let list = tickets;
    if (tab === 'open')     list = list.filter((t) => ['OPEN', 'ASSIGNED', 'IN_PROGRESS'].includes(t.status));
    if (tab === 'resolved') list = list.filter((t) => ['RESOLVED', 'CLOSED'].includes(t.status));
    if (tab === 'urgent')   list = list.filter((t) => t.priority === 'HIGH' || t.priority === 'CRITICAL');
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(
        (t) =>
          t.title?.toLowerCase().includes(q) ||
          t.ticket_number?.toLowerCase().includes(q) ||
          t.description?.toLowerCase().includes(q)
      );
    }
    return [...list].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  }, [tickets, tab, search]);

  const submitNew = async (e) => {
    e.preventDefault();
    if (!form.title.trim() || !form.description.trim() || !form.category) {
      showToast('Fill in all fields', 'error');
      return;
    }
    setSubmitting(true);
    try {
      await client.post('/tickets/', {
        title: form.title.trim(),
        description: form.description.trim(),
        category: parseInt(form.category, 10),
      });
      showToast('Ticket created', 'success');
      setShowModal(false);
      setForm({ title: '', description: '', category: '' });
      load();
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to create ticket', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const tabs = [
    { key: 'all',      label: 'All',      count: tickets.length },
    { key: 'open',     label: 'Open',     count: tickets.filter((t) => ['OPEN','ASSIGNED','IN_PROGRESS'].includes(t.status)).length },
    { key: 'resolved', label: 'Resolved', count: tickets.filter((t) => ['RESOLVED','CLOSED'].includes(t.status)).length },
    { key: 'urgent',   label: 'Urgent',   count: tickets.filter((t) => ['HIGH','CRITICAL'].includes(t.priority)).length },
  ];

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">Tickets</div>
          <div className="page-subtitle">Track and manage your support tickets.</div>
        </div>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          <Plus size={16} /> New ticket
        </button>
      </div>

      {/* Tabs + search */}
      <div
        className="flex items-center justify-between mb-4"
        style={{ marginBottom: 16, gap: 12, flexWrap: 'wrap' }}
      >
        <div className="flex" style={{ gap: 4 }}>
          {tabs.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className="btn btn-sm"
              style={{
                background: tab === t.key ? 'var(--brand-600)' : 'var(--bg-card)',
                color: tab === t.key ? '#fff' : 'var(--text)',
                border: `1px solid ${tab === t.key ? 'var(--brand-600)' : 'var(--border)'}`,
              }}
            >
              {t.label} <span style={{ opacity: 0.7, marginLeft: 4 }}>({t.count})</span>
            </button>
          ))}
        </div>

        <div style={{ position: 'relative', minWidth: 240 }}>
          <Search
            size={16}
            style={{
              position: 'absolute',
              left: 12,
              top: '50%',
              transform: 'translateY(-50%)',
              color: 'var(--text-subtle)',
            }}
          />
          <input
            type="text"
            placeholder="Search tickets…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ paddingLeft: 36 }}
          />
        </div>
      </div>

      {/* Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: 32 }} className="flex items-center gap-2 text-muted">
            <Loader2 size={16} className="spin" /> Loading tickets…
          </div>
        ) : filtered.length === 0 ? (
          <div style={{ padding: 48, textAlign: 'center' }}>
            <div className="text-muted" style={{ marginBottom: 8 }}>No tickets found</div>
            <div className="text-sm text-muted">
              {search ? 'Try a different search term.' : 'Create your first ticket to get started.'}
            </div>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="table">
              <thead>
                <tr>
                  <th>Ticket</th>
                  <th>Title</th>
                  <th>Status</th>
                  <th>Priority</th>
                  <th>SLA</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((t) => (
                  <tr key={t.id} onClick={() => navigate(`/tickets/${t.id}`)}>
                    <td className="text-sm font-medium">{t.ticket_number}</td>
                    <td>
                      <div className="font-medium text-sm">{t.title}</div>
                    </td>
                    <td><StatusBadge status={t.status} /></td>
                    <td><PriorityBadge priority={t.priority} /></td>
                    <td><SlaBadge status={t.sla_status} hours={t.hours_until_sla} /></td>
                    <td className="text-sm text-muted">
                      {new Date(t.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* New ticket modal */}
      {showModal && (
        <div
          onClick={() => !submitting && setShowModal(false)}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.5)',
            zIndex: 100,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 20,
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="card"
            style={{ width: '100%', maxWidth: 500, padding: 24 }}
          >
            <div className="flex items-center justify-between mb-4" style={{ marginBottom: 16 }}>
              <div className="font-semibold" style={{ fontSize: 18 }}>New ticket</div>
              <button
                className="icon-btn"
                onClick={() => !submitting && setShowModal(false)}
                aria-label="Close"
              >
                <X size={18} />
              </button>
            </div>
            <form onSubmit={submitNew}>
              <div className="form-group">
                <label className="form-label">Title</label>
                <input
                  type="text"
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  placeholder="Brief summary of the issue"
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Category</label>
                <select
                  value={form.category}
                  onChange={(e) => setForm({ ...form, category: e.target.value })}
                  required
                >
                  <option value="">Select a category…</option>
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Description</label>
                <textarea
                  rows={5}
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  placeholder="Describe the issue in detail — include area, when it started, what you've tried"
                  required
                  style={{ resize: 'vertical' }}
                />
              </div>
              <div className="flex justify-between gap-2" style={{ marginTop: 16 }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowModal(false)}
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? (
                    <><Loader2 size={14} className="spin" /> Creating…</>
                  ) : (
                    'Create ticket'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}