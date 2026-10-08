import { NavLink, useNavigate } from 'react-router-dom';
import {
  Archive,
  Compass,
  Plus,
  Search,
  Sparkles,
} from '../icons.js';
import { signOut } from '../services/api.js';
import { LogOut } from 'lucide-react';

function CampusMark() {
  return (
    <svg
      className="brand-symbol"
      viewBox="0 0 40 40"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M20 3.5c-7.5 0-13.5 6-13.5 13.4 0 9.8 13.5 19.6 13.5 19.6s13.5-9.8 13.5-19.6C33.5 9.5 27.5 3.5 20 3.5Z"
        stroke="currentColor"
        strokeWidth="2.1"
      />

      <circle
        cx="20"
        cy="16.8"
        r="5.8"
        stroke="currentColor"
        strokeWidth="2.1"
      />

      <path
        d="m17.3 16.8 1.8 1.8 3.8-4.1"
        stroke="currentColor"
        strokeWidth="2.1"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      <path
        d="M2 10h4M34 10h4M1 27h6M33 27h6"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        opacity=".56"
      />
    </svg>
  );
}

const navItems = [
  {
    to: '/',
    label: 'Explore board',
    icon: Compass,
    end: true,
  },
  {
    to: '/my-items',
    label: 'My items',
    icon: Archive,
  },
];

export default function Navbar() {
  const navigate = useNavigate();

  function handleSignOut() {
    signOut();
    navigate('/sign-in', { replace: true });
  }

  return (
    <aside className="sidebar" aria-label="Main navigation">

      {/* Brand */}
      <NavLink
        className="brand"
        to="/"
        aria-label="CampusFind home"
      >
        <CampusMark />

        <span className="brand-copy">
          <span className="brand-wordmark">
            campusfind
          </span>

          <span className="brand-tagline">
            Lost · found · back
          </span>
        </span>
      </NavLink>

      {/* Section title */}
      <span className="nav-section-label">
        Your campus
      </span>

      {/* Navigation */}
      <nav className="primary-nav">
        {navItems.map(
          ({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `nav-link${isActive ? ' active' : ''}`
              }
            >
              <Icon
                size={17}
                strokeWidth={1.8}
              />

              <span>
                {label}
              </span>
            </NavLink>
          )
        )}
      </nav>

      <div className="sidebar-spacer" />

      {/* Quick actions */}
      <div className="sidebar-quick-actions">

        <NavLink
          className="button button-primary button-block"
          to="/report-lost"
        >
          <Search size={15} />
          Report lost
        </NavLink>

        <NavLink
          className="button button-block"
          to="/report-found"
        >
          <Plus size={15} />
          Report found
        </NavLink>

      </div>

      {/* Sidebar information */}
      <button className="button button-block sidebar-signout" type="button" onClick={handleSignOut}>
        <LogOut size={15} />
        Sign out
      </button>

      <div className="sidebar-note">
        <Sparkles size={15} />

        <span>
          <strong>
            Photo-match hints
          </strong>

          Backend photo matching
          uses pHash + colour + text signals.
        </span>
      </div>

    </aside>
  );
}
