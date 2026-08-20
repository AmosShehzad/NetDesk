import { useEffect, useState, useCallback } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, BarChart, Bar,
} from 'recharts';
import { RefreshCw, AlertTriangle, Star, Radio, TrendingUp, Users, Zap, CheckCircle2 } from 'lucide-react';
import api from '../api/client';
import './StaffDashboard.css';

const STATUS_COLORS = {
  OPEN: '#3b82f6',
  IN_PROGRESS: '#f59e0b',
  RESOLVED: '#10b981',
  CLOSED: '#6b7280',
  ESCALATED: '#ef4444',
};
const PRIORITY_COLORS = {
  LOW: '#10b981',
  MEDIUM: '#3b82f6',
  HIGH: '#f59e0b',
  CRITICAL: '#ef4444',
};

function KpiCard({ icon: Icon, label, value, tone = 'default', sub }) {
  return (
    <div className={`kpi-card kpi-${tone}`}>
      <div className="kpi-icon"><Icon size={20} /></div>
      <div className="kpi-body">
        <div className="kpi-label">{label}</div>
        <div className="kpi-value">{value}</div>
        {sub && <div className="kpi-sub">{sub}</div>}
      </div>
    </div>
  );
}

export default function StaffDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      const res = await api.get('/dashboard/');
      setData(res.data);
      setLastUpdated(new Date());
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, 30000); // auto-refresh every 30s
    return () => clearInterval(id);
  }, [load]);

  if (loading) return <div className="dash-state">Loading dashboard…</div>;
  if (error) return <div className="dash-state dash-error">Error: {error}</div>;
  if (!data) return null;

  // Transform data for charts
  const volumeData = data.volume_series.map(d => ({
    date: d.date.slice(5), // MM-DD
    Created: d.created,
    Resolved: d.resolved,
  }));

  const statusData = Object.entries(data.status_counts || {}).map(([name, value]) => ({ name, value }));
  const priorityData = Object.entries(data.priority_counts || {}).map(([name, value]) => ({ name, value }));
  const agentData = (data.agent_workload || []).slice(0, 8).map(a => ({
    name: a.agent_name,
    Open: a.open_count,
  }));
  const aiPerfData = [
    { name: 'AI Resolved', value: data.ai_resolved_count || 0 },
    { name: 'Escalated', value: data.escalated_count || 0 },
  ];

  return (
    <div className="staff-dashboard">
      <div className="dash-header">
        <div>
          <h1>Staff Dashboard</h1>
          <p className="dash-subtitle">
            {lastUpdated && `Updated ${lastUpdated.toLocaleTimeString()}`}
          </p>
        </div>
        <button className="dash-refresh" onClick={load} title="Refresh">
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      {/* KPI row */}
      <div className="kpi-grid">
        <KpiCard icon={TrendingUp} label="Total Tickets" value={data.total_tickets} />
        <KpiCard icon={Zap} label="Open" value={data.open_tickets} tone="info" />
        <KpiCard
          icon={AlertTriangle}
          label="SLA Breaches"
          value={data.sla_breaches}
          tone={data.sla_breaches > 0 ? 'danger' : 'success'}
        />
        <KpiCard
          icon={CheckCircle2}
          label="AI Resolution Rate"
          value={`${data.ai_resolution_rate}%`}
          tone="success"
        />
        <KpiCard
          icon={Star}
          label="Avg Satisfaction"
          value={data.avg_satisfaction ? `${data.avg_satisfaction} / 5` : '—'}
          tone="info"
        />
        <KpiCard
          icon={Radio}
          label="Active Outages"
          value={data.active_outages}
          tone={data.active_outages > 0 ? 'warning' : 'default'}
        />
      </div>

      {/* Charts grid */}
      <div className="charts-grid">
        {/* 30-day volume */}
        <div className="chart-card chart-wide">
          <h3>Ticket Volume — Last 30 Days</h3>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={volumeData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={12} />
              <YAxis stroke="var(--text-muted)" fontSize={12} allowDecimals={false} />
              <Tooltip contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }} />
              <Legend />
              <Line type="monotone" dataKey="Created" stroke="#3b82f6" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="Resolved" stroke="#10b981" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Status donut */}
        <div className="chart-card">
          <h3>Tickets by Status</h3>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={statusData} dataKey="value" nameKey="name" innerRadius={50} outerRadius={85} paddingAngle={2}>
                {statusData.map((entry) => (
                  <Cell key={entry.name} fill={STATUS_COLORS[entry.name] || '#9ca3af'} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Priority bar */}
        <div className="chart-card">
          <h3>Tickets by Priority</h3>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={priorityData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={12} />
              <YAxis stroke="var(--text-muted)" fontSize={12} allowDecimals={false} />
              <Tooltip contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }} />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {priorityData.map((entry) => (
                  <Cell key={entry.name} fill={PRIORITY_COLORS[entry.name] || '#9ca3af'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* AI performance donut */}
        <div className="chart-card">
          <h3>AI Performance</h3>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={aiPerfData} dataKey="value" nameKey="name" innerRadius={50} outerRadius={85} paddingAngle={2}>
                <Cell fill="#10b981" />
                <Cell fill="#ef4444" />
              </Pie>
              <Tooltip contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Agent workload */}
        <div className="chart-card chart-wide">
          <h3><Users size={16} style={{ verticalAlign: '-3px', marginRight: 6 }} />Agent Workload (Open Tickets)</h3>
          {agentData.length === 0 ? (
            <div className="dash-empty">No agents currently assigned to open tickets.</div>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={agentData} layout="vertical" margin={{ left: 40 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis type="number" stroke="var(--text-muted)" fontSize={12} allowDecimals={false} />
                <YAxis type="category" dataKey="name" stroke="var(--text-muted)" fontSize={12} width={120} />
                <Tooltip contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }} />
                <Bar dataKey="Open" fill="#3b82f6" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Daily report */}
      {data.daily_report && (
        <div className="chart-card">
          <h3>Today ({data.daily_report.date})</h3>
          <p><strong>{data.daily_report.total_today}</strong> tickets created today.</p>
          {data.daily_report.urgent_today?.length > 0 && (
            <>
              <p style={{ marginTop: 12, marginBottom: 6 }}>Urgent tickets today:</p>
              <ul className="urgent-list">
                {data.daily_report.urgent_today.map(t => (
                  <li key={t.ticket_number}>
                    <span className={`pri pri-${t.priority.toLowerCase()}`}>{t.priority}</span>
                    <span className="tno">{t.ticket_number}</span>
                    <span>{t.title}</span>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}
    </div>
  );
}