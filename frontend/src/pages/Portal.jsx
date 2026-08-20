import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Ticket as TicketIcon,
  Clock,
  CheckCircle2,
  AlertTriangle,
  CreditCard,
  Plus,
  ArrowRight,
  Loader2,
} from 'lucide-react';
import client from '../api/client';

function StatCard({ icon: Icon, label, value, tone = 'brand' }) {
  const toneMap = {
    brand:   { bg: 'rgba(99,102,241,0.1)',  fg: 'var(--brand-600)' },
    success: { bg: 'rgba(16,185,129,0.12)', fg: 'var(--success)' },
    warning: { bg: 'rgba(245,158,11,0.12)', fg: 'var(--warning)' },
    danger:  { bg: 'rgba(239,68,68,0.12)',  fg: 'var(--danger)' },
  };
  const t = toneMap[tone];
  return (
    <div className="card card-hover stat-card">
      <div className="stat-icon" style={{ background: t.bg, color: t.fg }}>
        <Icon size={22} />
      </div>
      <div>
        <div className="stat-value">{value}</div>
        <div className="stat-label">{label}</div>
      </div>
    </div>
  );
}

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

export default function Portal() {
  const navigate = useNavigate();
  const [tickets, setTickets] = useState([]);
  const [bill, setBill] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const [tRes, bRes] = await Promise.allSettled([
          client.get('/tickets/?page_size=100'),
          client.get('/billing/'),
        ]);
        if (!mounted) return;
        if (tRes.status === 'fulfilled') {
          setTickets(tRes.value.data.results || tRes.value.data);
        }
        if (bRes.status === 'fulfilled') {
          const bills = bRes.value.data.results || bRes.value.data;
          setBill(Array.isArray(bills) && bills.length > 0 ? bills[0] : null);
        }
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, []);

  const total = tickets.length;
  const open = tickets.filter((t) => ['OPEN', 'ASSIGNED', 'IN_PROGRESS'].includes(t.status)).length;
  const resolved = tickets.filter((t) => ['RESOLVED', 'CLOSED'].includes(t.status)).length;
  const urgent = tickets.filter((t) => t.priority === 'HIGH' || t.priority === 'CRITICAL').length;

  const recent = [...tickets]
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .slice(0, 5);

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-muted">
        <Loader2 size={16} className="spin" /> Loading dashboard…
      </div>
    );
  }

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">Dashboard</div>
          <div className="page-subtitle">Here's what's happening with your account.</div>
        </div>
        <Link to="/tickets" className="btn btn-primary">
          <Plus size={16} /> New ticket
        </Link>
      </div>

      {/* Stat cards */}
      <div className="grid grid-4 mb-4" style={{ marginBottom: 24 }}>
        <StatCard icon={TicketIcon} label="Total tickets" value={total} tone="brand" />
        <StatCard icon={Clock} label="Open" value={open} tone="warning" />
        <StatCard icon={CheckCircle2} label="Resolved" value={resolved} tone="success" />
        <StatCard icon={AlertTriangle} label="Urgent" value={urgent} tone="danger" />
      </div>

      {/* Bill + Recent tickets */}
      <div className="grid grid-2" style={{ alignItems: 'start' }}>
        {/* Current bill */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4" style={{ marginBottom: 16 }}>
            <CreditCard size={18} style={{ color: 'var(--brand-600)' }} />
            <div className="font-semibold">Current bill</div>
          </div>
          {bill ? (
            <>
              <div style={{ fontSize: 28, fontWeight: 700, marginBottom: 8 }}>
                Rs. {Number(bill.amount ?? bill.total ?? 0).toLocaleString()}
              </div>
              <div className="text-sm text-muted">
                Status:{' '}
                <span
                  className={`badge ${
                    bill.status === 'PAID' ? 'badge-success' :
                    bill.status === 'OVERDUE' ? 'badge-danger' : 'badge-warning'
                  }`}
                >
                  {bill.status || 'PENDING'}
                </span>
              </div>
              {bill.due_date && (
                <div className="text-sm text-muted" style={{ marginTop: 8 }}>
                  Due: {new Date(bill.due_date).toLocaleDateString()}
                </div>
              )}
            </>
          ) : (
            <div className="text-muted text-sm" style={{ padding: '16px 0' }}>
              No bills yet.
            </div>
          )}
        </div>

        {/* Recent tickets */}
        <div className="card">
          <div className="flex items-center justify-between mb-4" style={{ marginBottom: 16 }}>
            <div className="font-semibold">Recent tickets</div>
            <Link to="/tickets" className="text-sm" style={{ color: 'var(--brand-600)' }}>
              View all <ArrowRight size={12} style={{ display: 'inline', verticalAlign: 'middle' }} />
            </Link>
          </div>
          {recent.length === 0 ? (
            <div className="text-muted text-sm" style={{ padding: '16px 0' }}>
              No tickets yet. Create one to get started.
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              {recent.map((t) => (
                <div
                  key={t.id}
                  onClick={() => navigate(`/tickets/${t.id}`)}
                  className="card-hover"
                  style={{
                    padding: '12px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border)',
                    cursor: 'pointer',
                  }}
                >
                  <div className="flex items-center justify-between gap-2">
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <div className="text-xs text-muted">{t.ticket_number}</div>
                      <div
                        className="font-medium text-sm"
                        style={{
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {t.title}
                      </div>
                    </div>
                    <StatusBadge status={t.status} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}