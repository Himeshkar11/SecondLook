import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../auth/AuthContext.jsx';

/**
 * Enterprise Portal Sidebar Navigation — Milestone 05
 * Role-aware navigation tailored to canonical BIDDER or OFFICER roles.
 * Never exposes officer routes to bidders, or bidder routes to officers.
 */
const BIDDER_NAV_ITEMS = [
  { path: '/bidder', label: 'Dashboard', icon: '📊' },
  { path: '/bidder/tenders', label: 'Tenders', icon: '📑' },
  { path: '/bidder/bids', label: 'My Bids', icon: '📝' },
  { path: '/bidder/compliance', label: 'Compliance', icon: '🛡️' },
  { path: '/bidder/documents', label: 'Documents', icon: '📁' },
  { path: '/bidder/profile', label: 'Profile', icon: '🏢' },
];

const OFFICER_NAV_ITEMS = [
  { path: '/officer', label: 'Dashboard', icon: '📊' },
  { path: '/officer/tenders', label: 'Tenders', icon: '📑' },
  { path: '/officer/bidders', label: 'Bidders', icon: '🏢' },
  { path: '/officer/evaluations', label: 'Evaluations', icon: '⚖️' },
  { path: '/officer/reviews', label: 'Requirement Review', icon: '🔍' },
  { path: '/officer/audit', label: 'Audit Trail', icon: '📋' },
  { path: '/settings', label: 'Profile & Settings', icon: '⚙️' },
];

const PUBLIC_NAV_ITEMS = [
  { path: '/login', label: 'Sign In', icon: '🔑' },
  { path: '/signup', label: 'Register', icon: '📝' },
];

export default function Sidebar({ isOpen, onCloseMobile }) {
  const { role, isAuthenticated, isAuthResolving } = useAuth();

  const navItems = role === 'BIDDER'
    ? BIDDER_NAV_ITEMS
    : role === 'OFFICER'
      ? OFFICER_NAV_ITEMS
      : isAuthenticated
        ? [{ path: '/settings', label: 'Account', icon: '⚙️' }]
        : PUBLIC_NAV_ITEMS;

  const sectionLabel = role === 'BIDDER'
    ? 'Bidder Navigation'
    : role === 'OFFICER'
      ? 'Officer Navigation'
      : isAuthenticated
        ? 'Account'
        : 'SecondLook Portal';

  return (
    <aside
      style={{
        width: 'var(--sidebar-width)',
        backgroundColor: 'var(--color-bg-sidebar)',
        borderRight: '1px solid var(--color-border)',
        display: 'flex',
        flexDirection: 'column',
        height: 'calc(100vh - var(--header-height))',
        position: 'sticky',
        top: 'var(--header-height)',
        flexShrink: 0,
        zIndex: 50,
      }}
      className={`sl-sidebar ${isOpen ? 'sl-sidebar-open' : ''}`}
    >
      <div style={{ padding: 'var(--space-3) var(--space-4)', borderBottom: '1px solid var(--color-border)' }}>
        <div
          style={{
            fontSize: 'var(--font-size-xs)',
            fontWeight: 'var(--font-weight-bold)',
            color: 'var(--color-text-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
          }}
        >
          {sectionLabel}
        </div>
      </div>

      <nav style={{ flex: 1, padding: 'var(--space-2) var(--space-2)', overflowY: 'auto' }}>
        {isAuthResolving ? (
          <div style={{ padding: 'var(--space-4)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
            Loading navigation...
          </div>
        ) : (
          <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
            {navItems.map((item) => (
              <li key={item.path} style={{ marginBottom: '2px' }}>
                <NavLink
                  to={item.path}
                  end={item.path === '/bidder' || item.path === '/officer'}
                  onClick={onCloseMobile}
                  style={({ isActive }) => ({
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--space-3)',
                    padding: 'var(--space-2) var(--space-3)',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: 'var(--font-size-sm)',
                    fontWeight: isActive ? 'var(--font-weight-semibold)' : 'var(--font-weight-normal)',
                    color: isActive ? 'var(--color-primary)' : 'var(--color-text-secondary)',
                    backgroundColor: isActive ? 'var(--color-primary-subtle)' : 'transparent',
                    borderLeft: isActive ? '3px solid var(--color-primary)' : '3px solid transparent',
                    textDecoration: 'none',
                    transition: 'background-color var(--transition-fast), color var(--transition-fast)',
                  })}
                >
                  <span style={{ fontSize: '14px', width: '18px', textAlign: 'center' }}>{item.icon}</span>
                  <span>{item.label}</span>
                </NavLink>
              </li>
            ))}
          </ul>
        )}
      </nav>

      <div
        style={{
          padding: 'var(--space-3) var(--space-4)',
          borderTop: '1px solid var(--color-border)',
          backgroundColor: 'var(--color-bg-subtle)',
          fontSize: 'var(--font-size-xs)',
          color: 'var(--color-text-muted)',
        }}
      >
        <span>SecondLook v0.1.0</span>
        <div style={{ fontSize: '11px', marginTop: '2px' }}>
          {role ? `${role} Role Active` : 'GeM Compliance Prototype'}
        </div>
      </div>
    </aside>
  );
}
