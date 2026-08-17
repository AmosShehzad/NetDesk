import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Inbox } from 'lucide-react';
import client from '../api/client';
import StatusBadge from '../components/StatusBadge';
import { useToast } from '../context/ToastContext';

export default function Tickets() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const { showToast } = useToast();

  const load = () => client.get('/tickets/')
    .then((res) => {
      setTickets(res.data.results || res.data);
      setLoading(false);
    })
    .catch((err) => {
      setLoading(false);
      showToast(err.response?.data?.detail || 'Failed to load tickets.');
    });

  useEffect(() => { load(); }, []);

  const createTicket = async (e) => {
  e.preventDefault();
  try {
    await client.post('/tickets/', { title, description, category: 1 });
    setTitle(''); setDescription(''); setShowForm(false);
    showToast('Ticket created successfully', 'success');
  } catch (err) {
    showToast('Failed to create ticket. Check the category.', 'error');
    return;
  }
  load(); // separate — a refresh failure won't be mistaken for a creation failure
};

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h2>Tickets</h2>
          <p style={{ color: 'var(--gray-500)', fontSize: 14, margin: '4px 0 0' }}>All support requests in one place.</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="btn btn-primary">
          {showForm ? 'Cancel' : '+ New ticket'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={createTicket} className="card card-pad" style={{ marginBottom: 20, display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="field">
            <label>Title</label>
            <input className="input" value={title} onChange={(e) => setTitle(e.target.value)} required />
          </div>
          <div className="field">
            <label>Description</label>
            <textarea rows={3} value={description} onChange={(e) => setDescription(e.target.value)} required />
          </div>
          <button type="submit" className="btn btn-primary" style={{ alignSelf: 'flex-start' }}>Submit ticket</button>
        </form>
      )}

      <div className="card">
        {loading ? (
          <div style={{ padding: 16 }}>
            {[1, 2, 3].map((i) => (
              <div key={i} className="skeleton" style={{ height: 44, marginBottom: 8 }} />
            ))}
          </div>
        ) : tickets.length === 0 ? (
          <div className="empty-state">
            <Inbox size={28} color="var(--gray-300)" style={{ marginBottom: 8 }} />
            <h3>No tickets yet</h3>
            <p>Create your first ticket to get started.</p>
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Ticket #</th>
                <th>Title</th>
                <th>Status</th>
                <th>Priority</th>
              </tr>
            </thead>
            <tbody>
              {tickets.map((t) => (
                <tr key={t.id}>
                  <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--gray-500)' }}>
                    <Link to={`/tickets/${t.id}`}>{t.ticket_number}</Link>
                  </td>
                  <td><Link to={`/tickets/${t.id}`}>{t.title}</Link></td>
                  <td><StatusBadge status={t.status} priority={t.priority} /></td>
                  <td>{t.priority}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}