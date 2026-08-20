import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft, Send, Sparkles, Loader2, Clock, User, Tag, AlertTriangle, Star,
} from 'lucide-react';
import client from '../api/client';
import { useAuth } from '../context/AuthContext';
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

export default function TicketDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const { showToast } = useToast();
  const [ticket, setTicket] = useState(null);
  const [comments, setComments] = useState([]);
  const [activities, setActivities] = useState([]);
  const [rating, setRating] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reply, setReply] = useState('');
  const [sending, setSending] = useState(false);

  // Rating state
  const [starHover, setStarHover] = useState(0);
  const [starValue, setStarValue] = useState(0);
  const [feedback, setFeedback] = useState('');
  const [ratingSubmitting, setRatingSubmitting] = useState(false);

  const load = async () => {
    try {
      const [tRes, cRes, aRes, rRes] = await Promise.allSettled([
        client.get(`/tickets/${id}/`),
        client.get(`/comments/?ticket=${id}`),
        client.get(`/activities/?ticket=${id}`),
        client.get(`/ratings/?ticket=${id}`),
      ]);
      if (tRes.status === 'fulfilled') setTicket(tRes.value.data);
      if (cRes.status === 'fulfilled') {
        const d = cRes.value.data.results || cRes.value.data;
        setComments(d);
      }
      if (aRes.status === 'fulfilled') {
        const d = aRes.value.data.results || aRes.value.data;
        setActivities(d);
      }
      if (rRes.status === 'fulfilled') {
        const d = rRes.value.data.results || rRes.value.data;
        if (Array.isArray(d) && d.length > 0) setRating(d[0]);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    load();
    const iv = setInterval(load, 15000); // poll for new AI replies
    return () => clearInterval(iv);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const sendReply = async (e) => {
    e.preventDefault();
    if (!reply.trim()) return;
    setSending(true);
    try {
      await client.post('/comments/', { ticket: parseInt(id, 10), message: reply.trim() });
      setReply('');
      load();
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to send reply', 'error');
    } finally {
      setSending(false);
    }
  };

  const submitRating = async (e) => {
    e.preventDefault();
    if (starValue < 1) {
      showToast('Please select a star rating', 'error');
      return;
    }
    setRatingSubmitting(true);
    try {
      await client.post('/ratings/', {
        ticket: parseInt(id, 10),
        stars: starValue,
        feedback: feedback.trim(),
      });
      showToast('Thanks for your feedback!', 'success');
      load();
    } catch (err) {
      showToast(err?.response?.data?.detail || 'Failed to submit rating', 'error');
    } finally {
      setRatingSubmitting(false);
    }
  };

  if (loading && !ticket) {
    return (
      <div className="flex items-center gap-2 text-muted">
        <Loader2 size={16} className="spin" /> Loading ticket…
      </div>
    );
  }

  if (!ticket) return <div className="text-muted">Ticket not found.</div>;

  const isAI = (c) =>
    c.author_username?.toLowerCase().includes('ai') ||
    c.author_username?.toLowerCase().includes('assistant');

  const isMine = (c) => c.author_username === user?.username;

  const isResolved = ['RESOLVED', 'CLOSED'].includes(ticket.status);
  const isCustomer = user?.role === 'CUSTOMER';

  return (
    <>
      {/* Header */}
      <div style={{ marginBottom: 16 }}>
        <Link to="/tickets" className="text-sm flex items-center gap-2" style={{ color: 'var(--text-muted)', width: 'fit-content' }}>
          <ArrowLeft size={14} /> Back to tickets
        </Link>
      </div>

      <div className="page-header">
        <div style={{ minWidth: 0, flex: 1 }}>
          <div className="text-xs text-muted" style={{ marginBottom: 4 }}>{ticket.ticket_number}</div>
          <div className="page-title" style={{ marginBottom: 8 }}>{ticket.title}</div>
          <div className="flex items-center gap-2" style={{ flexWrap: 'wrap' }}>
            <StatusBadge status={ticket.status} />
            <span className={`badge ${
              ticket.priority === 'CRITICAL' ? 'badge-danger' :
              ticket.priority === 'HIGH' ? 'badge-warning' :
              ticket.priority === 'MEDIUM' ? 'badge-info' : 'badge-muted'
            }`}>
              {ticket.priority}
            </span>
            {ticket.sla_status === 'BREACHED' && (
              <span className="badge badge-danger">
                <AlertTriangle size={12} /> SLA breached
              </span>
            )}
            {ticket.sla_status !== 'BREACHED' && ticket.sla_status !== 'RESOLVED' && (
              <span className="badge badge-muted">
                <Clock size={12} /> {ticket.hours_until_sla}h to SLA
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="grid" style={{ gridTemplateColumns: '1fr 320px', gap: 20, alignItems: 'start' }}>
        {/* Main chat area */}
        <div className="card" style={{ padding: 20 }}>
          <div className="font-semibold mb-4" style={{ marginBottom: 16 }}>Conversation</div>

          {/* Original description as first bubble */}
          <div className="chat-list" style={{ marginBottom: 16 }}>
            <div className="bubble bubble-in" style={{ maxWidth: '80%' }}>
              <div className="bubble-meta" style={{ marginBottom: 6 }}>
                {ticket.customer_username || 'Customer'} · {new Date(ticket.created_at).toLocaleString()}
              </div>
              <div>{ticket.description}</div>
            </div>

            {comments.map((c) => {
              const ai = isAI(c);
              const mine = isMine(c);
              const cls = ai ? 'bubble-ai' : (mine ? 'bubble-out' : 'bubble-in');
              return (
                <div key={c.id} className={`bubble ${cls}`}>
                  <div
                    className="bubble-meta flex items-center gap-2"
                    style={{
                      marginBottom: 6,
                      color: mine ? 'rgba(255,255,255,0.8)' : 'var(--text-subtle)',
                    }}
                  >
                    {ai && (
                      <span
                        className="badge badge-brand"
                        style={{ padding: '2px 6px', fontSize: 10 }}
                      >
                        <Sparkles size={10} /> AI
                      </span>
                    )}
                    <span>{c.author_username}</span>
                    <span>·</span>
                    <span>{new Date(c.created_at).toLocaleString()}</span>
                  </div>
                  <div style={{ whiteSpace: 'pre-wrap' }}>{c.message}</div>
                </div>
              );
            })}
          </div>

          {/* Reply composer */}
          {!isResolved && (
            <form onSubmit={sendReply} style={{ borderTop: '1px solid var(--border)', paddingTop: 16 }}>
              <textarea
                rows={3}
                value={reply}
                onChange={(e) => setReply(e.target.value)}
                placeholder="Type your reply…"
                style={{ resize: 'vertical', marginBottom: 8 }}
              />
              <div className="flex justify-between items-center gap-2">
                <div className="text-xs text-muted">Enter to add a new line, click Send to submit.</div>
                <button type="submit" className="btn btn-primary" disabled={sending || !reply.trim()}>
                  {sending ? <Loader2 size={14} className="spin" /> : <Send size={14} />}
                  {sending ? 'Sending…' : 'Send'}
                </button>
              </div>
            </form>
          )}

          {/* Rating widget */}
          {isResolved && isCustomer && !rating && (
            <div style={{ borderTop: '1px solid var(--border)', paddingTop: 20, marginTop: 8 }}>
              <div className="font-semibold mb-2">How was your support experience?</div>
              <div className="text-sm text-muted mb-4" style={{ marginBottom: 12 }}>
                Rate this ticket so we can improve.
              </div>
              <form onSubmit={submitRating}>
                <div className="flex gap-2 mb-4" style={{ marginBottom: 12 }}>
                  {[1, 2, 3, 4, 5].map((n) => (
                    <button
                      type="button"
                      key={n}
                      onClick={() => setStarValue(n)}
                      onMouseEnter={() => setStarHover(n)}
                      onMouseLeave={() => setStarHover(0)}
                      style={{ padding: 4 }}
                    >
                      <Star
                        size={28}
                        fill={(starHover || starValue) >= n ? '#f59e0b' : 'none'}
                        color={(starHover || starValue) >= n ? '#f59e0b' : 'var(--text-subtle)'}
                      />
                    </button>
                  ))}
                </div>
                <textarea
                  rows={2}
                  value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                  placeholder="Any feedback? (optional)"
                  style={{ resize: 'vertical', marginBottom: 8 }}
                />
                <button type="submit" className="btn btn-primary" disabled={ratingSubmitting}>
                  {ratingSubmitting ? <Loader2 size={14} className="spin" /> : null}
                  Submit rating
                </button>
              </form>
            </div>
          )}

          {rating && (
            <div style={{ borderTop: '1px solid var(--border)', paddingTop: 16, marginTop: 8 }}>
              <div className="flex items-center gap-2">
                {[1, 2, 3, 4, 5].map((n) => (
                  <Star key={n} size={16} fill={n <= rating.stars ? '#f59e0b' : 'none'} color="#f59e0b" />
                ))}
                <span className="text-sm text-muted">Your rating</span>
              </div>
              {rating.feedback && (
                <div className="text-sm text-muted" style={{ marginTop: 8 }}>
                  "{rating.feedback}"
                </div>
              )}
            </div>
          )}
        </div>

        {/* Side panel */}
        <div className="flex flex-col gap-4">
          {/* Details */}
          <div className="card">
            <div className="font-semibold mb-4" style={{ marginBottom: 12 }}>Details</div>
            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-2 text-sm">
                <User size={14} style={{ color: 'var(--text-muted)' }} />
                <span className="text-muted">Customer:</span>
                <span>{ticket.customer_username || '—'}</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <User size={14} style={{ color: 'var(--text-muted)' }} />
                <span className="text-muted">Agent:</span>
                <span>{ticket.assigned_agent_username || 'Unassigned'}</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Tag size={14} style={{ color: 'var(--text-muted)' }} />
                <span className="text-muted">Category:</span>
                <span>{ticket.category_name || `#${ticket.category}`}</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Clock size={14} style={{ color: 'var(--text-muted)' }} />
                <span className="text-muted">SLA:</span>
                <span>
                  {ticket.sla_deadline
                    ? new Date(ticket.sla_deadline).toLocaleString()
                    : '—'}
                </span>
              </div>
            </div>
          </div>

          {/* Activity timeline */}
          <div className="card">
            <div className="font-semibold mb-4" style={{ marginBottom: 12 }}>Activity</div>
            {activities.length === 0 ? (
              <div className="text-sm text-muted">No activity yet.</div>
            ) : (
              <div className="flex flex-col" style={{ gap: 12 }}>
                {activities.map((a) => (
                  <div key={a.id} className="flex" style={{ gap: 10 }}>
                    <div
                      style={{
                        width: 8, height: 8, borderRadius: '50%',
                        background: 'var(--brand-500)',
                        marginTop: 6, flexShrink: 0,
                      }}
                    />
                    <div style={{ minWidth: 0 }}>
                      <div className="text-sm font-medium" style={{ textTransform: 'capitalize' }}>
                        {a.action?.replace(/_/g, ' ')}
                      </div>
                      {a.details && (
                        <div className="text-xs text-muted" style={{ marginTop: 2 }}>{a.details}</div>
                      )}
                      <div className="text-xs" style={{ color: 'var(--text-subtle)', marginTop: 2 }}>
                        {new Date(a.created_at).toLocaleString()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}