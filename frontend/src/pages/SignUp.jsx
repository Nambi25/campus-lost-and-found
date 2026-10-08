import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { UserPlus } from 'lucide-react';
import { signUp } from '../services/api.js';

export default function SignUp() {
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ name: '', email: '', password: '', confirmPassword: '', rollNo: '', phone: '' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  function update(key, value) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    if (form.password !== form.confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    setBusy(true);
    try {
      await signUp(form);
      navigate(location.state?.from?.pathname || '/', { replace: true });
    } catch (err) {
      setError(err.message || 'Unable to create account.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card surface-card">
        <div className="auth-mark" aria-hidden="true"><UserPlus size={22} /></div>
        <p className="eyebrow">CampusFind</p>
        <h1>Create your campus account</h1>
        <p className="lead">Your account is stored in the application database and is used to sign in on this system.</p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="form-field"><span>Full name</span><input className="form-control" value={form.name} onChange={(e) => update('name', e.target.value)} placeholder="Your name" autoComplete="name" required /></label>
          <label className="form-field"><span>Email</span><input className="form-control" type="email" value={form.email} onChange={(e) => update('email', e.target.value)} placeholder="you@campus.edu" autoComplete="email" required /></label>
          <div className="form-grid">
            <label className="form-field"><span>Roll number <small>(optional)</small></span><input className="form-control" value={form.rollNo} onChange={(e) => update('rollNo', e.target.value)} placeholder="23CSE001" /></label>
            <label className="form-field"><span>Phone <small>(optional)</small></span><input className="form-control" type="tel" value={form.phone} onChange={(e) => update('phone', e.target.value)} placeholder="Phone number" /></label>
          </div>
          <label className="form-field"><span>Password</span><input className="form-control" type="password" value={form.password} onChange={(e) => update('password', e.target.value)} placeholder="At least 6 characters" autoComplete="new-password" minLength={6} required /></label>
          <label className="form-field"><span>Confirm password</span><input className="form-control" type="password" value={form.confirmPassword} onChange={(e) => update('confirmPassword', e.target.value)} placeholder="Re-enter password" autoComplete="new-password" minLength={6} required /></label>
          {error && <p className="field-error auth-error">{error}</p>}
          <button className="button button-primary button-block" type="submit" disabled={busy}>
            <UserPlus size={15} />
            {busy ? 'Creating account…' : 'Create account'}
          </button>
        </form>

        <p className="auth-switch">Already have an account? <Link to="/sign-in">Sign in</Link></p>
      </div>
    </div>
  );
}
