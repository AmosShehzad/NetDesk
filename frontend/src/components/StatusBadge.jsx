const COLORS = {
  OPEN: 'var(--status-open)',
  ASSIGNED: 'var(--status-open)',
  IN_PROGRESS: 'var(--status-progress)',
  WAITING_CUSTOMER: 'var(--status-progress)',
  RESOLVED: 'var(--status-resolved)',
  CLOSED: 'var(--status-closed)',
};

export default function StatusBadge({ status, priority }) {
  const color = priority === 'CRITICAL' ? 'var(--status-critical)' : (COLORS[status] || 'var(--gray-500)');
  return (
    <span className="status-badge">
      <span className="status-dot" style={{ background: color }} />
      {status.replace('_', ' ')}
    </span>
  );
}