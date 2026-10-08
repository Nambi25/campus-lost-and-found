import { useState } from 'react';
import { Navigate, Link, useLocation, useNavigate } from 'react-router-dom';
import { LogIn, Sparkles } from 'lucide-react';
import { DEMO_EMAIL, DEMO_PASSWORD, demoSignIn, getStoredAuth, signIn } from '../services/api.js';

export default function SignIn() {
  const navigate = useNavigate();
  const location = useLocation();
  const existing = getStoredAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  if (existing) {
    return <Navigate to={location.state?.from?.pathname || '/'} replace />;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setBusy(true);
    try {
      await signIn(email.trim(), password);
      navigate(location.state?.from?.pathname || '/', { replace: true });
    } catch (err) {
      setError(err.message || 'Unable to sign in.');
    } finally {
      setBusy(false);
    }
  }

  async function handleDemo() {
    setError('');
    setBusy(true);
    try {
      await demoSignIn();
      navigate('/', { replace: true });
    } catch (err) {
      setError(err.message || 'Unable to start the demo account.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card surface-card">
        <div className="auth-mark" aria-hidden="true"><LogIn size={22} /></div>
        <p className="eyebrow">CampusFind</p>
        <h1>Sign in to your campus board</h1>
        <p className="lead">Sign in to access the dashboard, report items, manage claims, and view your items.</p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="form-field">
            <span>Email</span>
            <input className="form-control" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@campus.edu" autoComplete="email" required />
          </label>
          <label className="form-field">
            <span>Password</span>
            <input className="form-control" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Your password" autoComplete="current-password" required />
          </label>
          {error && <p className="field-error auth-error">{error}</p>}
          <button className="button button-primary button-block" type="submit" disabled={busy}>
            <LogIn size={15} />
            {busy ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <div className="auth-divider"><span>or</span></div>

        <button className="button button-block" type="button" onClick={handleDemo} disabled={busy}>
          <Sparkles size={15} />
          Use demo account
        </button>
        <p className="auth-demo-note">Demo: {DEMO_EMAIL} · {DEMO_PASSWORD}</p>
        <p className="auth-switch">New to CampusFind? <Link to="/sign-up" state={{ from: location.state?.from }}>Create an account</Link></p>
      </div>
    </div>
  );
}
