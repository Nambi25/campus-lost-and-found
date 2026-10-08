import { Clock3, MapPin } from '../icons.js';
import { Link } from 'react-router-dom';

function relativeTime(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Just now';
  const minutes = Math.max(1, Math.floor((Date.now() - date.getTime()) / 60000));
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return days < 7 ? `${days}d ago` : date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

export function TypePill({ kind }) {
  return <span className={`type-pill ${kind === 'found' ? 'type-found' : 'type-lost'}`}>{kind === 'found' ? 'Found' : 'Lost'}</span>;
}

export function StatusPill({ status, label }) {
  const text = label || (status === 'resolved' ? 'Resolved' : 'Active');
  const visualState = ['pending', 'approved', 'rejected', 'resolved'].includes(status) ? status : 'active';
  return <span className={`status-pill status-${visualState}`}><span className="status-dot" />{text}</span>;
}

export default function ItemCard({ item }) {
  return (
    <article className="item-card">
      <Link className="item-card-link" to={`/items/${item.id}`} aria-label={`${item.kind} item: ${item.title}`}>
        <div className="item-card-image">
          {item.imageUrl ? <img src={item.imageUrl} alt={item.title} loading="lazy" /> : <div className="image-fallback" aria-hidden="true">{item.emoji || '◈'}</div>}
          <span className="image-type">{item.kind === 'found' ? 'Campus find' : 'Looking for'}</span>
        </div>
        <div className="item-card-body">
          <div className="item-card-title-row">
            <h3>{item.title}</h3>
            <TypePill kind={item.kind} />
          </div>
          <p className="item-card-description">{item.description}</p>
          <div className="item-card-meta">
            <span className="meta-part"><MapPin size={12} />{item.location}</span>
            <span className="meta-part"><Clock3 size={12} />{relativeTime(item.reportedAt)}</span>
          </div>
          <div className="item-card-meta item-card-bottom-meta">
            <span>{item.category}</span>
            <StatusPill status={item.status} label={item.status === 'resolved' ? 'Resolved' : item.claims?.some((claim) => claim.status === 'pending') ? 'Claim pending' : 'Open'} />
          </div>
        </div>
      </Link>
    </article>
  );
}
