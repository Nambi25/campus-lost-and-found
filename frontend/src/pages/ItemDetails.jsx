import { useEffect, useState } from 'react';
import { ArrowLeft, Check, Clock3, MapPin, MessageCircle, PackageCheck, ShieldCheck, Sparkles, X } from '../icons.js';
import { Link, useParams } from 'react-router-dom';
import { StatusPill, TypePill } from '../components/ItemCard.jsx';
import { createClaim, DEMO_USER_ID, findPotentialMatches, getItem, updateClaimStatus } from '../services/api.js';

function exactDate(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Time not specified' : date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
}

function claimLabel(item) {
  if (item.claims.some((claim) => claim.status === 'approved')) return 'Claim approved';
  if (item.claims.some((claim) => claim.status === 'pending')) return 'Claim pending';
  if (item.claims.some((claim) => claim.status === 'rejected')) return 'Claim reviewed';
  return 'No claims yet';
}

export default function ItemDetails() {
  const { id } = useParams();
  const [item, setItem] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [claimOpen, setClaimOpen] = useState(false);
  const [details, setDetails] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const isOwner = item?.posterId === DEMO_USER_ID;
  const existingClaim = item?.claims.find((claim) => claim.claimantId === DEMO_USER_ID);

  const refresh = async () => {
    const [record, matches] = await Promise.all([getItem(id), findPotentialMatches(id)]);
    setItem(record);
    setSuggestions(matches.matches);
  };
  useEffect(() => { refresh(); }, [id]);

  const submitClaim = async (event) => {
    event.preventDefault();
    if (details.trim().length < 12) {
      setError('Add a specific identifying detail (at least 12 characters).');
      return;
    }
    setBusy(true);
    setError('');
    try {
      await createClaim(id, { details });
      await refresh();
      setClaimOpen(false);
      setDetails('');
    } catch (problem) {
      setError(problem.message);
    } finally {
      setBusy(false);
    }
  };

  const review = async (claimId, status) => {
    setBusy(true);
    setError('');
    try { await updateClaimStatus(id, claimId, status); await refresh(); }
    catch (problem) { setError(problem.message); }
    finally { setBusy(false); }
  };

  if (!item) return <div className="page-wrap"><div className="details-topline"><Link className="back-link" to="/"><ArrowLeft size={14} /> Back to the board</Link></div><div className="empty-state"><div className="empty-icon"><PackageCheck size={21} /></div><h3>That report isn’t on the board</h3><p>It may have been removed or the link may be out of date.</p><Link className="button button-small" to="/">Explore reports</Link></div></div>;

  return (
    <div className="page-wrap">
      <div className="details-topline"><Link className="back-link" to="/"><ArrowLeft size={14} /> Back to the board</Link><span>/</span><span>Report details</span></div>
      <div className="detail-layout">
        <div>
          <div className="detail-photo">
            {item.imageUrl ? <img src={item.imageUrl} alt={item.title} /> : <div className="image-fallback" aria-label="No photo provided">{item.emoji || '◈'}<span className="tiny">No photo provided</span></div>}
            <div className="detail-photo-caption"><TypePill kind={item.kind} /><span className="tiny">{item.imageUrl ? `Photo shared by ${item.posterName}` : 'No item photo provided'}</span></div>
          </div>
          {suggestions.length > 0 && <section className="surface-card detail-card" style={{ marginTop: 13 }}>
            <div className="match-note-top"><span className="match-mode">Suggested matches · backend matching</span><Sparkles size={16} /></div>
            <p className="field-hint">Suggestions compare category, nearby campus spot, and description words. The backend uses image hashes, colour similarity, and text/category similarity.</p>
            <div className="match-list">{suggestions.map(({ item: match, score, reason }) => <Link className="match-item" to={`/items/${match.id}`} key={match.id}>
              {match.imageUrl ? <img src={match.imageUrl} alt="" /> : <div className="match-thumb-fallback" aria-hidden="true">{match.emoji || '◈'}</div>}<span className="match-item-copy"><strong>{match.title}</strong><span>{reason}</span></span><span className="match-score">{Math.round(score * 100)}%</span>
            </Link>)}</div>
          </section>}
        </div>
        <div className="detail-copy">
          <section className="surface-card detail-card">
            <div className="detail-title-row"><div><TypePill kind={item.kind} /><h1>{item.title}</h1></div><StatusPill status={item.status} /></div>
            <p className="detail-description">{item.description}</p>
            <div className="detail-meta-grid">
              <div className="detail-meta"><MapPin size={16} /><span>Campus spot<strong>{item.location}</strong></span></div>
              <div className="detail-meta"><Clock3 size={16} /><span>Posted<strong>{exactDate(item.reportedAt)}</strong></span></div>
              <div className="detail-meta"><Clock3 size={16} /><span>{item.kind === 'found' ? 'Found around' : 'Last seen'}<strong>{exactDate(item.eventAt)}</strong></span></div>
              <div className="detail-meta"><ShieldCheck size={16} /><span>Claim state<strong>{claimLabel(item)}</strong></span></div>
            </div>
            <button className="button button-primary button-block detail-action" type="button" disabled={item.status === 'resolved' || isOwner || Boolean(existingClaim)} onClick={() => setClaimOpen((value) => !value)}>
              <MessageCircle size={15} />{existingClaim ? `Your claim · ${existingClaim.status}` : item.status === 'resolved' ? 'Report marked resolved' : isOwner ? 'You posted this report' : 'I think this is mine'}
            </button>
            {claimOpen && !isOwner && <form className="claim-form" onSubmit={submitClaim}>
              <h3>Help the owner verify it</h3>
              <p className="field-hint">Share a detail that wasn’t included in the public description. Don’t enter student ID numbers or other sensitive information.</p>
              <p className="field-hint">Your signed-in CampusFind account is attached to this claim.</p>
              <label className="form-field">What detail shows it’s yours?<textarea className="form-textarea" value={details} onChange={(event) => setDetails(event.target.value)} placeholder="A mark, contents, or detail only the owner would know…" /></label>
              {error && <span className="field-error" role="alert">{error}</span>}
              <button className="button button-primary" type="submit" disabled={busy}>{busy ? 'Sending…' : 'Send claim for review'}</button>
            </form>}
          </section>
          {error && !claimOpen && <div className="field-error" role="alert">{error}</div>}
          {isOwner && <section className="surface-card detail-card">
            <h3><ShieldCheck size={16} /> Claim requests <span className="muted tiny">({item.claims.length})</span></h3>
            {item.claims.length === 0 ? <p className="field-hint">No one has submitted a claim yet. Any identifying detail they share is visible to you here.</p> : <div className="claim-list">{item.claims.map((claim) => <article className="claim-row" key={claim.id}>
              <div className="claim-row-top"><strong>{claim.claimantName}</strong><span className={`status-pill ${claim.status === 'pending' ? 'status-pending' : claim.status === 'approved' ? 'status-approved' : 'status-rejected'}`}>{claim.status}</span></div>
              <p>{claim.details}</p>
              {claim.status === 'pending' && <div className="claim-actions"><button className="button button-primary button-small" type="button" disabled={busy} onClick={() => review(claim.id, 'approved')}><Check size={13} /> Approve</button><button className="button button-danger button-small" type="button" disabled={busy} onClick={() => review(claim.id, 'rejected')}><X size={13} /> Reject</button></div>}
            </article>)}</div>}
            <div className="notice-card" style={{ marginTop: 12 }}><ShieldCheck size={14} /><span>Review the private detail, then arrange a safe handoff. This demo is not official campus identity verification.</span></div>
          </section>}
          {!isOwner && <div className="notice-card"><ShieldCheck size={14} /><span>Claim notes are stored by the backend for the reporting student to review.</span></div>}
        </div>
      </div>
    </div>
  );
}
