import React from 'react';
import { NavLink } from 'react-router-dom';

/**
 * Enterprise Portal Sidebar Navigation
 * Preserves all existing React Router routes:
 * Dashboard, Tenders, Bidders, Documents, Verification, Audit, Settings
 */
const NAV_ITEMS = [
  { path: '/dashboard', label: 'Dashboard', icon: '📊' },
  { path: '/tenders', label: 'Tenders', icon: '📑' },
  { path: '/bidders', label: 'Bidders', icon: '🏢' },
  { path: '/documents', label: 'Documents', icon: '📁' },
  { path: '/verification', label: 'Verification', icon: '🛡️' },
  { path: '/audit', label: 'Audit Log', icon: '📋' },
  { path: '/settings', label: 'Settings', icon: '⚙️' },
];

export default function Sidebar({ isOpen, onCloseMobile }) {
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
        <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Compliance Navigation
        </div>
      </div>

      <nav style={{ flex: 1, padding: 'var(--space-2) var(--space-2)', overflowY: 'auto' }}>
        <ul style={{ listStyle: 'none' }}>
          {NAV_ITEMS.map((item) => (
            <li key={item.path} style={{ marginBottom: '2px' }}>
              <NavLink
                to={item.path}
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
        <div style={{ fontSize: '11px', marginTop: '2px' }}>GeM Compliance Prototype</div>
      </div>
    </aside>
  );
}
