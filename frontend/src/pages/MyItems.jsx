import { useEffect, useState } from 'react';
import { Archive, ArrowUpRight, Check, Clock3, MapPin, PackageCheck, ShieldCheck, X } from '../icons.js';
import { Link } from 'react-router-dom';
import { getMyItems, updateClaimStatus, updateItemStatus } from '../services/api.js';
import { StatusPill, TypePill } from '../components/ItemCard.jsx';

export default function MyItems() {
  const [data, setData] = useState({ reports: [], claims: [] });
  const [view, setView] = useState('all');
  const [error, setError] = useState('');
  const [busyId, setBusyId] = useState('');
  const refresh = async () => setData(await getMyItems());
  useEffect(() => { refresh(); }, []);

  const updateStatus = async (item, status) => {
    setBusyId(item.id); setError('');
    try { await updateItemStatus(item.id, status); await refresh(); }
    catch (problem) { setError(problem.message); }
    finally { setBusyId(''); }
  };
  const reviewClaim = async (claim, status) => {
    setBusyId(claim.id); setError('');
    try { await updateClaimStatus(claim.itemId, claim.id, status); await refresh(); }
    catch (problem) { setError(problem.message); }
    finally { setBusyId(''); }
  };

  const visibleReports = data.reports.filter((item) => view === 'all' || item.status === view);
  const pendingClaims = data.reports.flatMap((item) => item.claims.filter((claim) => claim.status === 'pending').map((claim) => ({ ...claim, itemId: item.id, itemTitle: item.title })));
  const activeCount = data.reports.filter((item) => item.status === 'active').length;

  return (
    <div className="page-wrap">
      <header className="page-header">
        <div className="page-header-copy"><p className="eyebrow">Your demo activity</p><h1>My items.</h1><p className="lead">Keep an eye on your reports and the students who’ve shared a clue. Changes stay in this browser.</p></div>
        <Link className="button button-primary" to="/report-found"><PackageCheck size={15} /> Add a found item</Link>
      </header>
      <section className="dashboard-stats" aria-label="Your report statistics">
        <div className="dashboard-stat"><div><span>Your reports</span><strong>{data.reports.length}</strong></div><Archive size={18} /></div>
        <div className="dashboard-stat"><div><span>Still active</span><strong>{activeCount}</strong></div><MapPin size={18} /></div>
        <div className="dashboard-stat"><div><span>Claims to review</span><strong>{pendingClaims.length}</strong></div><ShieldCheck size={18} /></div>
      </section>
      {error && <div className="notice-card" role="alert"><ShieldCheck size={14} /><span>{error}</span></div>}
      <section aria-labelledby="reports-heading">
        <div className="dashboard-section-heading"><h2 id="reports-heading">Your reports</h2><Link className="back-link tiny" to="/"><span>Browse board</span><ArrowUpRight size={13} /></Link></div>
        <div className="dashboard-tabs" role="tablist" aria-label="Filter your reports">
          {[['all', 'All reports'], ['active', 'Active'], ['resolved', 'Resolved']].map(([value, label]) => <button key={value} type="button" role="tab" aria-selected={view === value} className={`dashboard-tab${view === value ? ' active' : ''}`} onClick={() => setView(value)}>{label}</button>)}
        </div>
        <div className="my-items-list">
          {visibleReports.map((item) => <article className="my-item-row" key={item.id}>
            <div className="my-item-thumb">{item.imageUrl ? <img src={item.imageUrl} alt="" /> : <span aria-hidden="true">{item.emoji || "◈"}</span>}</div>
            <div className="my-item-copy"><div style={{ display: 'flex', alignItems: 'center', gap: 7, flexWrap: 'wrap' }}><TypePill kind={item.kind} /><StatusPill status={item.status} /></div><h3><Link to={`/items/${item.id}`}>{item.title}</Link></h3><div className="my-item-meta"><span><MapPin size={11} /> {item.location}</span><span><Clock3 size={11} /> {item.claims.filter((claim) => claim.status === 'pending').length} pending claim(s)</span></div></div>
            <div className="my-item-actions"><Link className="button button-small" to={`/items/${item.id}`}>View report</Link><button className="button button-small" type="button" disabled={busyId === item.id} onClick={() => updateStatus(item, item.status === 'active' ? 'resolved' : 'active')}>{item.status === 'active' ? 'Mark resolved' : 'Reopen'}</button></div>
          </article>)}
          {!visibleReports.length && <div className="empty-state"><div className="empty-icon"><Archive size={20} /></div><h3>No reports in this view</h3><p>Reports you create in this demo will appear here with their claim activity.</p><Link className="button button-small" to="/report-lost">Report a lost item</Link></div>}
        </div>
      </section>
      <section aria-labelledby="claims-heading" style={{ marginTop: 30 }}>
        <div className="dashboard-section-heading"><h2 id="claims-heading">Claims on your reports</h2><span className="status-pill status-pending">{pendingClaims.length} pending</span></div>
        <div className="my-items-list">
          {pendingClaims.map((claim) => <article className="claim-preview" key={claim.id}>
            <p><strong>{claim.claimantName}</strong> has a detail for <Link className="back-link" to={`/items/${claim.itemId}`}>{claim.itemTitle}</Link><br /><span className="muted">“{claim.details}”</span></p>
            <div className="claim-actions"><button className="button button-primary button-small" type="button" disabled={busyId === claim.id} onClick={() => reviewClaim(claim, 'approved')}><Check size={13} /> Approve</button><button className="button button-danger button-small" type="button" disabled={busyId === claim.id} onClick={() => reviewClaim(claim, 'rejected')}><X size={13} /> Reject</button></div>
          </article>)}
          {!pendingClaims.length && <div className="empty-state"><div className="empty-icon"><ShieldCheck size={20} /></div><h3>Nothing waiting for review</h3><p>If another student submits a claim on your report, their verification detail will show up here.</p></div>}
        </div>
      </section>
      {data.claims.length > 0 && <section aria-labelledby="your-claims-heading" style={{ marginTop: 30 }}>
        <div className="dashboard-section-heading"><h2 id="your-claims-heading">Claims you submitted</h2></div>
        <div className="my-items-list">{data.claims.map((claim) => <article className="my-item-row" key={claim.id}>
          <div className="my-item-thumb">{claim.itemImageUrl ? <img src={claim.itemImageUrl} alt="" /> : <span aria-hidden="true">◈</span>}</div><div className="my-item-copy"><StatusPill status={claim.status} label={`Claim ${claim.status}`} /><h3>{claim.itemTitle}</h3><div className="my-item-meta"><span>Submitted {new Date(claim.submittedAt).toLocaleDateString()}</span></div></div><Link className="button button-small" to={`/items/${claim.itemId}`}>View <ArrowUpRight size={12} /></Link>
        </article>)}</div>
      </section>}
      <div className="notice-card" style={{ marginTop: 24 }}><ShieldCheck size={14} /><span>Demo data is saved in this browser only. A real school-wide service needs a server, durable storage, and account-based access controls.</span></div>
    </div>
  );
}
