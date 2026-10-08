import { useNavigate } from 'react-router-dom';
import { ShieldCheck, Tag, Users } from '../icons.js';
import ItemForm from '../components/ItemForm.jsx';
import { createItem } from '../services/api.js';

export default function ReportLost() {
  const navigate = useNavigate();
  const submit = async (values) => {
    const item = await createItem(values);
    navigate(`/items/${item.id}`);
  };
  return (
    <div className="page-wrap report-page">
      <header className="page-header">
        <div className="page-header-copy"><p className="eyebrow">Start the search</p><h1>Report a lost item.</h1><p className="lead">Add an optional photo and the last place you remember it. The board can help connect your report to a find nearby.</p></div>
      </header>
      <div className="form-layout">
        <ItemForm kind="lost" onSubmit={submit} />
        <aside className="form-aside">
          <section className="surface-card guide-card">
            <h3><Tag size={16} /> Better clues, better matches</h3>
            <ul className="guide-list">
              <li><ShieldCheck size={14} /><span>Keep one unique mark private. You can use it to review a claim later.</span></li>
              <li><Users size={14} /><span>Add a nearby building or landmark so found reports are easier to compare.</span></li>
              <li><Tag size={14} /><span>A recent, well-lit photo is helpful, but optional. Add one if you have it.</span></li>
            </ul>
          </section>
          <div className="notice-card"><ShieldCheck size={15} /><span>Claims in this prototype are notes for the reporting student, not official campus identity verification.</span></div>
        </aside>
      </div>
    </div>
  );
}
