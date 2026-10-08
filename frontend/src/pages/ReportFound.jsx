import { useNavigate } from 'react-router-dom';
import { MapPin, ShieldCheck, Sparkles } from '../icons.js';
import ItemForm from '../components/ItemForm.jsx';
import { createItem } from '../services/api.js';

export default function ReportFound() {
  const navigate = useNavigate();
  const submit = async (values) => {
    const item = await createItem(values);
    navigate(`/items/${item.id}`);
  };
  return (
    <div className="page-wrap report-page">
      <header className="page-header">
        <div className="page-header-copy"><p className="eyebrow">Put a find on the map</p><h1>Report a found item.</h1><p className="lead">A few specific clues can save somebody a long afternoon. Add the item and where you left it safe.</p></div>
      </header>
      <div className="form-layout">
        <ItemForm kind="found" onSubmit={submit} />
        <aside className="form-aside">
          <section className="surface-card guide-card">
            <h3><Sparkles size={16} /> Help the right person spot it</h3>
            <ul className="guide-list">
              <li><MapPin size={14} /><span>Include a building, floor, room, or nearby landmark.</span></li>
              <li><ShieldCheck size={14} /><span>Keep one identifying detail back; ask the claimant to describe it.</span></li>
              <li><Sparkles size={14} /><span>We’ll surface reports with similar item details and campus locations.</span></li>
            </ul>
          </section>
          <div className="notice-card"><ShieldCheck size={15} /><span>Don’t post student ID numbers, access codes, or other sensitive details in the description.</span></div>
        </aside>
      </div>
    </div>
  );
}
