import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Badge from '../common/Badge.jsx';
import { useAuth } from '../../auth/AuthContext.jsx';

/**
 * Enterprise Portal Header — Milestone 05
 * Features:
 * - Role-aware Logo navigation (/bidder for BIDDER, /officer for OFFICER)
 * - Light / Dark Theme toggle with localStorage persistence
 * - National Tricolor Accent Bar
 * - Role status chip & authenticated user identity
 * - Centralized sign out
 */
export default function Header({ onToggleSidebar }) {
  const navigate = useNavigate();
  const { user, role, isAuthenticated, signOut } = useAuth();
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('secondlook-theme') || 'light';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('secondlook-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  const handleSignOut = async () => {
    await signOut();
    navigate('/login');
  };

  const logoDestination = role === 'BIDDER' ? '/bidder' : role === 'OFFICER' ? '/officer' : '/';

  return (
    <header
      style={{
        backgroundColor: 'var(--color-bg-header)',
        borderBottom: '1px solid var(--color-border)',
        height: 'var(--header-height)',
        display: 'flex',
        flexDirection: 'column',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}
    >
      {/* Subtle National Accent Line */}
      <div style={{ display: 'flex', height: '3px', width: '100%' }}>
        <div style={{ flex: 1, backgroundColor: 'var(--gov-saffron-bright)' }} />
        <div style={{ flex: 1, backgroundColor: '#FFFFFF' }} />
        <div style={{ flex: 1, backgroundColor: 'var(--gov-green)' }} />
      </div>

      <div
        style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 var(--space-4)',
        }}
      >
        {/* Left: Mobile Toggle & Logo Navigation */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <button
            type="button"
            onClick={onToggleSidebar}
            style={{
              padding: 'var(--space-1) var(--space-2)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--color-text-secondary)',
              backgroundColor: 'var(--color-bg-subtle)',
            }}
            aria-label="Toggle navigation drawer"
          >
            ☰
          </button>

          {/* Clickable Logo navigating to role workspace */}
          <Link
            to={logoDestination}
            style={{
              display: 'flex',
              alignItems: 'baseline',
              gap: 'var(--space-2)',
              textDecoration: 'none',
            }}
          >
            <span
              style={{
                fontSize: 'var(--font-size-base)',
                fontWeight: 'var(--font-weight-bold)',
                color: 'var(--color-primary)',
                letterSpacing: '-0.01em',
              }}
            >
              SecondLook
            </span>
            <span
              style={{
                fontSize: 'var(--font-size-xs)',
                color: 'var(--color-text-muted)',
                fontWeight: 'var(--font-weight-normal)',
                display: 'none',
              }}
              className="sl-header-sub"
            >
              | GeM Tender &amp; Bidder Compliance
            </span>
          </Link>
        </div>

        {/* Right: Theme Toggle, Role Badge & User Area */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          {/* Theme Toggle Button */}
          <button
            type="button"
            onClick={toggleTheme}
            style={{
              padding: 'var(--space-1) var(--space-3)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border)',
              backgroundColor: 'var(--color-bg-subtle)',
              color: 'var(--color-text-primary)',
              fontSize: 'var(--font-size-xs)',
              fontWeight: 'var(--font-weight-medium)',
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-1)',
            }}
            aria-label="Toggle light/dark theme"
          >
            <span>{theme === 'dark' ? '☀️' : '🌙'}</span>
            <span>{theme === 'dark' ? 'Light' : 'Dark'}</span>
          </button>

          {role === 'OFFICER' ? (
            <Badge variant="primary">OFFICER</Badge>
          ) : role === 'BIDDER' ? (
            <Badge variant="success">BIDDER</Badge>
          ) : isAuthenticated ? (
            <Badge variant="warning">NO ROLE</Badge>
          ) : (
            <Badge variant="info">Demo Portal</Badge>
          )}

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-2)',
              fontSize: 'var(--font-size-sm)',
              color: 'var(--color-text-secondary)',
              borderLeft: '1px solid var(--color-border)',
              paddingLeft: 'var(--space-3)',
            }}
          >
            <div
              style={{
                width: '24px',
                height: '24px',
                borderRadius: 'var(--radius-full)',
                backgroundColor: 'var(--color-primary-subtle)',
                color: 'var(--color-primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 'var(--font-weight-bold)',
                fontSize: 'var(--font-size-xs)',
              }}
            >
              {user?.email?.slice(0, 2).toUpperCase() || '??'}
            </div>
            <span style={{ fontWeight: 'var(--font-weight-medium)' }}>
              {user?.email || 'Unauthenticated'}
            </span>
            {isAuthenticated ? (
              <button
                type="button"
                onClick={handleSignOut}
                style={{
                  padding: 'var(--space-1) var(--space-2)',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--color-border)',
                  color: 'var(--color-text-secondary)',
                  fontSize: 'var(--font-size-xs)',
                  cursor: 'pointer',
                  backgroundColor: 'var(--color-bg-subtle)',
                }}
              >
                Sign out
              </button>
            ) : (
              <Link to="/login" style={{ fontSize: 'var(--font-size-xs)' }}>
                Sign in
              </Link>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
