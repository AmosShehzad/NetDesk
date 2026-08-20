import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, Clock, UserPlus, PlayCircle, ArrowUpCircle, RefreshCw } from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import './AgentQueue.css';

const STATUS_TABS = [
  { key: '', label: 'All Active' },
  { key: 'OPEN', label: 'Open' },
  { key: 'IN_PROGRESS', label: 'In Progress' },
  { key: 'ESCALATED', label: 'Escalated' },
];

function slaLabel(row) {
  if (row.sla_breached) return { text: 'BREACHED', tone: 'danger' };
  if (row.sla_hours_remaining == null) return { text: 'No SLA', tone: 'muted' };
  const h = row.sla_hours_remaining;
  if (h < 2) return { text: `${h}h left`, tone: 'danger' };
  if (h < 8) return { text: `${h}h left`, tone: 'warning' };
  return { text: `${h}h left`, tone: 'success' };
}

export default function AgentQueue() {
  const { user } = useAuth();
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [busyId, setBusyId] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      const params = statusFilter ? { status: statusFilter } : {};
      const res = await api.get('/tickets/queue/', { params });
      setRows(res.data.results || []);
      setLastUpdated(new Date());
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'Failed to load queue');
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    setLoading(true);
    load();
    const id = setInterval(load, 30000);
    return () => clearInterval(id);
  }, [load]);

  const doAction = async (ticketId, patch) => {
    setBusyId(ticketId);
    try {
      await api.patch(`/tickets/${ticketId}/`, patch);
      await load();
    } catch (e) {
      alert(e.response?.data?.detail || e.message || 'Action failed');
    } finally {
      setBusyId(null);
    }
  };

  const assignToMe = (t) => doAction(t.id, { assigned_agent: user.id });
  const markInProgress = (t) => doAction(t.id, { status: 'IN_PROGRESS' });
  const escalate = (t) => doAction(t.id, { escalated: true, status: 'ESCALATED' });

  return (
    <div className="queue-page">
      <div className="queue-header">
        <div>
          <h1>Agent Queue</h1>
          <p className="queue-subtitle">
            {rows.length} active ticket{rows.length !== 1 ? 's' : ''}
            {lastUpdated && ` · updated ${lastUpdated.toLocaleTimeString()}`}
          </p>
        </div>
        <button className="queue-refresh" onClick={load}>
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      <div className="queue-tabs">
        {STATUS_TABS.map(t => (
          <button
            key={t.key || 'all'}
            className={`queue-tab ${statusFilter === t.key ? 'active' : ''}`}
            onClick={() => setStatusFilter(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {loading && <div className="queue-state">Loading queue...</div>}
      {error && <div className="queue-state queue-error">Error: {error}</div>}

      {!loading && !error && rows.length === 0 && (
        <div className="queue-state">No active tickets. Nice work.</div>
      )}

      {!loading && !error && rows.length > 0 && (
        <div className="queue-table">
          <div className="qt-head">
            <div>SLA</div>
            <div>Ticket</div>
            <div>Customer</div>
            <div>Priority</div>
            <div>Status</div>
            <div>Agent</div>
            <div>Actions</div>
          </div>

          {rows.map(t => {
            const sla = slaLabel(t);
            const isBreached = t.sla_breached;
            return (
              <div key={t.id} className={`qt-row ${isBreached ? 'qt-row-breached' : ''}`}>
                <div className={`sla-pill sla-${sla.tone}`}>
                  {isBreached ? <AlertTriangle size={12} /> : <Clock size={12} />}
                  {sla.text}
                </div>

                <div className="qt-ticket">
                  <Link to={`/tickets/${t.id}`} className="qt-ticket-link">
                    <span className="tno">{t.ticket_number}</span>
                    <span className="ttitle">{t.title}</span>
                  </Link>
                </div>

                <div className="qt-muted">{t.customer_username || '—'}</div>

                <div>
                  <span className={`pri pri-${t.priority.toLowerCase()}`}>{t.priority}</span>
                </div>

                <div>
                  <span className={`stat stat-${t.status.toLowerCase()}`}>
                    {t.status.replace('_', ' ')}
                  </span>
                </div>

                <div className="qt-muted">
                  {t.assigned_agent_username || <em style={{ opacity: 0.6 }}>unassigned</em>}
                </div>

                <div className="qt-actions">
                  {!t.assigned_agent && user?.role !== 'CUSTOMER' && (
                    <button
                      className="qt-btn"
                      onClick={() => assignToMe(t)}
                      disabled={busyId === t.id}
                      title="Assign to me"
                    >
                      <UserPlus size={14} />
                    </button>
                  )}
                  {t.status === 'OPEN' && (
                    <button
                      className="qt-btn"
                      onClick={() => markInProgress(t)}
                      disabled={busyId === t.id}
                      title="Mark in progress"
                    >
                      <PlayCircle size={14} />
                    </button>
                  )}
                  {!t.escalated && (
                    <button
                      className="qt-btn qt-btn-danger"
                      onClick={() => escalate(t)}
                      disabled={busyId === t.id}
                      title="Escalate"
                    >
                      <ArrowUpCircle size={14} />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}