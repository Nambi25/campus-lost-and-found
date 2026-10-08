import { useEffect, useState } from 'react';
import { ArrowUpRight, PackageCheck, Search, Sparkles } from '../icons.js';
import { Link } from 'react-router-dom';
import ItemCard from '../components/ItemCard.jsx';
import SearchBar from '../components/SearchBar.jsx';
import { getBoardStats, listItems } from '../services/api.js';

const DEFAULT_FILTERS = { query: '', kind: 'all', category: 'all', location: 'all', recency: 'all', claimState: 'all' };

export default function Home() {
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [items, setItems] = useState([]);
  const [stats, setStats] = useState({ active: 0, found: 0, lost: 0, claims: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    Promise.all([listItems(filters), getBoardStats()]).then(([reports, boardStats]) => {
      if (!alive) return;
      setItems(reports);
      setStats(boardStats);
      setLoading(false);
    });
    return () => { alive = false; };
  }, [filters]);

  return (
    <div className="page-wrap">
      <section className="home-hero">
        <div className="hero-copy">
          <p className="eyebrow">Campus lost & found · live board</p>
          <h1>Search campus.<br /><span>Skip the group-chat scroll.</span></h1>
          <p className="lead">Lost something between classes? Found a small piece of somebody’s day? Put it on the board and help it find its way back.</p>
          <div className="hero-actions">
            <Link className="button button-primary" to="/report-lost"><Search size={15} /> I lost something</Link>
            <Link className="button" to="/report-found"><PackageCheck size={15} /> I found something</Link>
          </div>
        </div>
        <div className="hero-art" aria-label={`${stats.active} active reports on the campus board`}>
          <span className="hero-count"><span className="footer-signal" /> Campus board · demo</span>
          <strong>{stats.active} active reports</strong>
          <span>{stats.found} found · {stats.lost} still looking</span>
        </div>
      </section>

      <section aria-labelledby="board-title">
        <div className="section-heading">
          <div><h2 id="board-title">Around campus</h2><p>Reports shared by students, sorted by newest first.</p></div>
          <span className="status-pill status-active"><span className="status-dot" /> {stats.claims} claims to review</span>
        </div>
        <SearchBar filters={filters} onChange={setFilters} />
        <div className="feed-layout">
          <div>
            <div className="result-caption"><span>{loading ? 'Looking through the board…' : `${items.length} ${items.length === 1 ? 'report' : 'reports'} found`}</span><span>Photos when available + details · demo data</span></div>
            <div className="feed-list">
              {!loading && items.map((item) => <ItemCard key={item.id} item={item} />)}
              {!loading && !items.length && <div className="empty-state"><div className="empty-icon"><Search size={21} /></div><h3>No reports match those filters</h3><p>Try another word, a wider time range, or clear one of the campus filters.</p><button className="button button-small" type="button" onClick={() => setFilters(DEFAULT_FILTERS)}>Clear search</button></div>}
            </div>
          </div>
          <aside className="feed-aside" aria-label="Board information">
            <section className="surface-card match-note">
              <div className="match-note-top"><span className="match-mode">Match hints</span><Sparkles size={16} /></div>
              <h3>Lookalikes, surfaced.</h3>
              <p>CampusFind compares item details and images to suggest reports that might be connected. Matching runs in the backend.</p>
              <Link className="button button-small button-block" to="/report-lost">Add a lost-item report <ArrowUpRight size={13} /></Link>
            </section>
            <div className="stat-strip" aria-label="Campus board counts">
              <div className="stat-row"><span>Found and waiting</span><strong>{stats.found}</strong></div>
              <div className="stat-row"><span>Still looking</span><strong>{stats.lost}</strong></div>
              <div className="stat-row"><span>Open claims</span><strong>{stats.claims}</strong></div>
            </div>
          </aside>
        </div>
      </section>
    </div>
  );
}
