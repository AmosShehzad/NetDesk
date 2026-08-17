import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import client from '../api/client';
import { useAuth } from '../context/AuthContext';
import StatusBadge from '../components/StatusBadge';

export default function TicketDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const [ticket, setTicket] = useState(null);
  const [comments, setComments] = useState([]);
  const [message, setMessage] = useState('');
  const [waitingForAI, setWaitingForAI] = useState(false);
  const scrollRef = useRef(null);
  const pollRef = useRef(null);

  const load = useCallback(async (silent = false) => {
    if (!silent) client.get(`/tickets/${id}/`).then((res) => setTicket(res.data));
    const res = await client.get(`/comments/?ticket=${id}`);
    const newComments = res.data.results || res.data;

    // If a new AI comment just arrived, stop showing the typing indicator
    setComments((prev) => {
      if (newComments.length > prev.length) setWaitingForAI(false);
      return newComments;
    });
  }, [id]);

  useEffect(() => { load(); }, [id, load]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [comments, waitingForAI]);

  // Poll for new messages every 3s ONLY while waiting on an AI reply — keeps it snappy without hammering the server constantly
  useEffect(() => {
    if (waitingForAI) {
      pollRef.current = setInterval(() => load(true), 3000);
    } else if (pollRef.current) {
      clearInterval(pollRef.current);
    }
    return () => clearInterval(pollRef.current);
  }, [waitingForAI, load]);

  const postComment = async (e) => {
    e.preventDefault();
    if (!message.trim()) return;
    const wasCustomer = user?.role === 'CUSTOMER';
    await client.post('/comments/', { ticket: id, message });
    setMessage('');
    if (wasCustomer) setWaitingForAI(true); // customer messages trigger an AI reply on the backend
    load();
  };

  if (!ticket) return <div className="empty-state">Loading…</div>;

  return (
    <div style={{ maxWidth: 680 }}>
      <Link to="/tickets" style={{ fontSize: 13, color: 'var(--gray-500)', textDecoration: 'none' }}>&larr; All tickets</Link>

      <div className="card card-pad" style={{ margin: '16px 0 20px' }}>
        <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--gray-500)', fontSize: 13, marginBottom: 6 }}>{ticket.ticket_number}</div>
        <h2 style={{ marginBottom: 10 }}>{ticket.title}</h2>
        <StatusBadge status={ticket.status} priority={ticket.priority} />
        {ticket.escalated && (
          <span className="status-badge" style={{ marginLeft: 12, color: 'var(--status-critical)' }}>
            <span className="status-dot" style={{ background: 'var(--status-critical)' }} /> Escalated to support team
          </span>
        )}
        <p style={{ color: 'var(--gray-700)', marginTop: 16, lineHeight: 1.6 }}>{ticket.description}</p>
      </div>

      <div className="chat-container" ref={scrollRef}>
        {comments.map((c) => {
          const isMine = c.author === user?.id;
          const isAI = c.author_username === 'AI Assistant';
          return (
            <div key={c.id} className={`chat-bubble-row ${isMine ? 'mine' : ''}`}>
              <div>
                <div className={`chat-bubble ${isMine ? 'mine' : isAI ? 'ai' : 'theirs'}`}>
                  {c.message}
                </div>
                <div className={`chat-meta ${isMine ? 'mine' : ''}`}>
                  {isAI ? '🤖 AI Assistant' : c.author_username} · {new Date(c.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          );
        })}
        {waitingForAI && (
          <div className="chat-bubble-row">
            <div className="typing-indicator">
              <span className="typing-dot"></span><span className="typing-dot"></span><span className="typing-dot"></span>
            </div>
          </div>
        )}
      </div>

      <form onSubmit={postComment} className="comment-composer">
        <input className="input" value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Type a message…" />
        <button type="submit" className="btn btn-primary">Send</button>
      </form>
    </div>
  );
}