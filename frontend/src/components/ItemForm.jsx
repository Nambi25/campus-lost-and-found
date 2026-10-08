import { useRef, useState } from 'react';
import { Check, ImagePlus, Info, MapPin, Upload } from '../icons.js';

const categories = ['Electronics', 'School supplies', 'Bags & accessories', 'Clothing', 'Keys & cards', 'Other'];
const MAX_IMAGE_BYTES = 3 * 1024 * 1024;

function localDateTime() {
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  return now.toISOString().slice(0, 16);
}

function fileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error('Could not read that image. Please choose another file.'));
    reader.readAsDataURL(file);
  });
}

export default function ItemForm({ kind, onSubmit }) {
  const inputRef = useRef(null);
  const [fields, setFields] = useState({ title: '', category: 'Electronics', description: '', location: '', timestamp: localDateTime() });
  const [imageFile, setImageFile] = useState(null);
  const [imageUrl, setImageUrl] = useState('');
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState('');
  const [saving, setSaving] = useState(false);
  const isFound = kind === 'found';

  const update = (key, value) => {
    setFields((current) => ({ ...current, [key]: value }));
    setErrors((current) => ({ ...current, [key]: '' }));
  };

  const chooseImage = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      setErrors((current) => ({ ...current, image: 'Choose an image file such as JPG, PNG, or WebP.' }));
      event.target.value = '';
      return;
    }
    if (file.size > MAX_IMAGE_BYTES) {
      setErrors((current) => ({ ...current, image: 'For this browser-only demo, choose an image under 3 MB.' }));
      event.target.value = '';
      return;
    }
    try {
      const dataUrl = await fileAsDataUrl(file);
      setImageFile(file);
      setImageUrl(dataUrl);
      setErrors((current) => ({ ...current, image: '' }));
    } catch (error) {
      setErrors((current) => ({ ...current, image: error.message }));
    }
  };

  const submit = async (event) => {
    event.preventDefault();
    const nextErrors = {};
    if (fields.title.trim().length < 3) nextErrors.title = 'Add an item name (at least 3 characters).';
    if (!fields.category) nextErrors.category = 'Choose an item category.';
    if (fields.description.trim().length < 12) nextErrors.description = 'Add a few identifying details (at least 12 characters).';
    if (!fields.location.trim()) nextErrors.location = 'Add the campus spot where it was last seen or found.';
    if (!fields.timestamp) nextErrors.timestamp = 'Add the approximate date and time.';
    if (isFound && !imageUrl) nextErrors.image = 'Add one clear photo so another student can recognize it.';
    setErrors(nextErrors);
    setFormError('');
    if (Object.keys(nextErrors).length) return;

    setSaving(true);
    try {
      await onSubmit({
        ...fields,
        title: fields.title.trim(),
        description: fields.description.trim(),
        location: fields.location.trim(),
        imageUrl,
        imageName: imageFile?.name || '',
        kind,
      });
    } catch (error) {
      setFormError(error.message || 'Could not save this report. Please try a smaller image.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <form className="surface-card form-card" onSubmit={submit} noValidate>
      <div className="form-card-header">
        <div className="form-card-icon"><MapPin size={18} /></div>
        <div><h2>{isFound ? 'A few details about the find' : 'Help us picture what went missing'}</h2><p>Clear details make it easier for the right student to spot a match.</p></div>
      </div>
      <div className="form-grid">
        <div className="form-field full">
          <label htmlFor="item-title">Item name <span className="required">*</span></label>
          <input id="item-title" className="form-control" value={fields.title} onChange={(event) => update('title', event.target.value)} placeholder="e.g. Graphite scientific calculator" maxLength={90} aria-invalid={Boolean(errors.title)} />
          {errors.title && <span className="field-error">{errors.title}</span>}
        </div>
        <div className="form-field">
          <label htmlFor="item-category">Category <span className="required">*</span></label>
          <select id="item-category" className="form-control" value={fields.category} onChange={(event) => update('category', event.target.value)}>
            {categories.map((category) => <option key={category}>{category}</option>)}
          </select>
        </div>
        <div className="form-field">
          <label htmlFor="item-location">Campus spot <span className="required">*</span></label>
          <input id="item-location" className="form-control" value={fields.location} onChange={(event) => update('location', event.target.value)} placeholder="Building, room, or landmark" maxLength={100} aria-invalid={Boolean(errors.location)} />
          {errors.location && <span className="field-error">{errors.location}</span>}
        </div>
        <div className="form-field full">
          <label htmlFor="item-description">Description <span className="required">*</span></label>
          <textarea id="item-description" className="form-textarea" value={fields.description} onChange={(event) => update('description', event.target.value)} placeholder={isFound ? 'Add details that can help the owner recognize it. Keep one distinctive detail private for claim review.' : 'Describe its color, brand, marks, case, or contents. Keep one distinctive detail private for claim review.'} maxLength={600} aria-invalid={Boolean(errors.description)} />
          <span className="field-hint">{fields.description.length}/600 · Tip: hold one specific detail back so the owner can verify a claim.</span>
          {errors.description && <span className="field-error">{errors.description}</span>}
        </div>
        <div className="form-field">
          <label htmlFor="item-timestamp">When was it {isFound ? 'found' : 'last seen'}? <span className="required">*</span></label>
          <input id="item-timestamp" className="form-control" type="datetime-local" value={fields.timestamp} onChange={(event) => update('timestamp', event.target.value)} aria-invalid={Boolean(errors.timestamp)} />
          <span className="field-hint">Approximate time is okay.</span>
          {errors.timestamp && <span className="field-error">{errors.timestamp}</span>}
        </div>
        <div className="form-field">
          <label htmlFor="item-photo">Item photo {!isFound && <span className="muted tiny">(optional)</span>}{isFound && <span className="required">*</span>}</label>
          <label className="image-upload" htmlFor="item-photo">
            {imageUrl ? <>
              <img className="image-preview" src={imageUrl} alt="Preview of the item you selected" />
              <span className="image-preview-cover"><span>{imageFile?.name || 'Photo ready'}</span><span><Upload size={13} /> Change photo</span></span>
            </> : <span className="image-upload-copy"><ImagePlus size={22} /><strong>{isFound ? "Choose a clear item photo" : "Add an item photo (optional)"}</strong><span>JPG, PNG, or WebP · up to 3 MB</span></span>}
            <input id="item-photo" ref={inputRef} type="file" accept="image/*" onChange={chooseImage} />
          </label>
          {errors.image && <span className="field-error">{errors.image}</span>}
        </div>
        {formError && <div className="form-field full"><span className="field-error" role="alert">{formError}</span></div>}
      </div>
      <div className="notice-card" style={{ marginTop: 16 }}><Info size={15} /><span>This prototype saves your photo, when provided, and report in this browser only. Don’t add student ID numbers or sensitive personal information.</span></div>
      <div className="form-actions">
        <button className="button button-primary" type="submit" disabled={saving}>{saving ? 'Saving…' : <><Check size={15} /> Post {isFound ? 'found' : 'lost'} report</>}</button>
      </div>
    </form>
  );
}
