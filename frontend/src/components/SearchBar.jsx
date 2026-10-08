import { Filter, Search, X } from '../icons.js';

const categories = ['Electronics', 'School supplies', 'Bags & accessories', 'Clothing', 'Keys & cards', 'Other'];
const locations = ['North Hall', 'West Hall', 'Student Union', 'Library', 'Science Building', 'Athletics Center', 'Other campus spot'];

export default function SearchBar({ filters, onChange }) {
  const set = (key, value) => onChange({ ...filters, [key]: value });
  const isFiltered = Object.entries(filters).some(([key, value]) => key === 'query' ? Boolean(value.trim()) : value !== 'all');
  const clear = () => onChange({ query: '', kind: 'all', category: 'all', location: 'all', recency: 'all', claimState: 'all' });

  return (
    <section className="search-panel" aria-label="Search and filter reports">
      <div className="search-main">
        <label className="search-input-wrap">
          <Search size={17} aria-hidden="true" />
          <span className="sr-only">Search by item, description, or campus place</span>
          <input value={filters.query} onChange={(event) => set('query', event.target.value)} placeholder="Search items, details, places…" />
        </label>
        <span className="filter-heading"><Filter size={15} /> Filters</span>
      </div>
      <div className="filter-grid">
        <label className="filter-label">Report type
          <select value={filters.kind} onChange={(event) => set('kind', event.target.value)}>
            <option value="all">Lost + found</option><option value="lost">Lost items</option><option value="found">Found items</option>
          </select>
        </label>
        <label className="filter-label">Category
          <select value={filters.category} onChange={(event) => set('category', event.target.value)}>
            <option value="all">All categories</option>{categories.map((category) => <option key={category} value={category}>{category}</option>)}
          </select>
        </label>
        <label className="filter-label">Campus spot
          <select value={filters.location} onChange={(event) => set('location', event.target.value)}>
            <option value="all">Everywhere</option>{locations.map((location) => <option key={location} value={location}>{location}</option>)}
          </select>
        </label>
        <label className="filter-label">When
          <select value={filters.recency} onChange={(event) => set('recency', event.target.value)}>
            <option value="all">Any time</option><option value="today">Today</option><option value="week">Past 7 days</option><option value="month">Past 30 days</option>
          </select>
        </label>
        <label className="filter-label">Claim state
          <select value={filters.claimState} onChange={(event) => set('claimState', event.target.value)}>
            <option value="all">Any claim state</option><option value="none">No claims</option><option value="pending">Claim pending</option><option value="approved">Claim approved</option>
          </select>
        </label>
        <button className="clear-filters" type="button" onClick={clear} disabled={!isFiltered} aria-label="Clear search and filters"><X size={13} /> Clear</button>
      </div>
    </section>
  );
}
