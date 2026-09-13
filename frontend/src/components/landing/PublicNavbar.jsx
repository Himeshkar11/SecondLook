import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

/**
 * PublicNavbar — Milestone 06
 * Pure public navigation for landing page visitors.
 * Features:
 * - SecondLook brand identity + national tricolor accent bar
 * - Semantic section anchors: Product, How It Works, Evidence, For Bidders, For Officers
 * - Dedicated role CTAs: Sign In, Sign Up as Bidder, Sign Up as Officer
 * - Theme toggle (Light / Dark)
 * - Mobile responsive drawer
 */
export default function PublicNavbar() {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('secondlook-theme') || 'light';
  });
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('secondlook-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  const navLinks = [
    { label: 'How It Works', href: '#how-it-works' },
    { label: 'Evidence Chain', href: '#evidence' },
    { label: 'AI + Human Control', href: '#human-control' },
    { label: 'For Bidders', href: '#for-bidders' },
    { label: 'For Officers', href: '#for-officers' },
  ];

  return (
    <header
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 100,
        backgroundColor: 'var(--color-bg-header)',
        borderBottom: '1px solid var(--color-border)',
        backdropFilter: 'blur(8px)',
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
          maxWidth: 'var(--max-content-width)',
          margin: '0 auto',
          padding: '0 var(--space-4)',
          height: 'var(--header-height)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        {/* Brand Logo */}
        <Link
          to="/"
          style={{
            display: 'flex',
            alignItems: 'baseline',
            gap: 'var(--space-2)',
            textDecoration: 'none',
          }}
        >
          <span
            style={{
              fontSize: 'var(--font-size-lg)',
              fontWeight: 'var(--font-weight-bold)',
              color: 'var(--color-primary)',
              letterSpacing: '-0.02em',
            }}
          >
            SecondLook
          </span>
          <span
            style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--color-text-muted)',
              fontWeight: 'var(--font-weight-normal)',
            }}
            className="sl-header-sub"
          >
            | Tender &amp; Bidder Compliance
          </span>
        </Link>

        {/* Desktop Nav Links */}
        <nav
          style={{
            display: 'none',
            alignItems: 'center',
            gap: 'var(--space-5)',
          }}
          className="sl-public-nav-desktop"
        >
          {navLinks.map((link) => (
            <a
              key={link.href}
              href={link.href}
              style={{
                fontSize: 'var(--font-size-sm)',
                fontWeight: 'var(--font-weight-medium)',
                color: 'var(--color-text-secondary)',
                textDecoration: 'none',
                transition: 'color var(--transition-fast)',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--color-primary)')}
              onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--color-text-secondary)')}
            >
              {link.label}
            </a>
          ))}
        </nav>

        {/* Right CTAs & Theme Toggle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          {/* Theme Toggle Button */}
          <button
            type="button"
            onClick={toggleTheme}
            style={{
              padding: 'var(--space-1) var(--space-2)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border)',
              backgroundColor: 'var(--color-bg-subtle)',
              color: 'var(--color-text-primary)',
              fontSize: 'var(--font-size-xs)',
              fontWeight: 'var(--font-weight-medium)',
              display: 'flex',
              alignItems: 'center',
              cursor: 'pointer',
            }}
            aria-label="Toggle light/dark theme"
          >
            <span>{theme === 'dark' ? '☀️' : '🌙'}</span>
          </button>

          {/* Sign In Link */}
          <Link
            to="/login"
            style={{
              fontSize: 'var(--font-size-sm)',
              fontWeight: 'var(--font-weight-medium)',
              color: 'var(--color-text-primary)',
              textDecoration: 'none',
              padding: 'var(--space-1) var(--space-3)',
            }}
          >
            Sign In
          </Link>

          {/* Preselected Role Signup CTAs */}
          <Link
            to="/signup?role=bidder"
            style={{
              display: 'none',
              padding: 'var(--space-1) var(--space-3)',
              borderRadius: 'var(--radius-sm)',
              fontSize: 'var(--font-size-xs)',
              fontWeight: 'var(--font-weight-semibold)',
              color: 'var(--color-success)',
              backgroundColor: 'var(--color-success-subtle)',
              border: '1px solid var(--color-success)',
              textDecoration: 'none',
              transition: 'transform var(--transition-fast)',
            }}
            className="sl-public-cta-bidder"
          >
            Bidder Signup
          </Link>

          <Link
            to="/signup?role=officer"
            style={{
              display: 'none',
              padding: 'var(--space-1) var(--space-3)',
              borderRadius: 'var(--radius-sm)',
              fontSize: 'var(--font-size-xs)',
              fontWeight: 'var(--font-weight-semibold)',
              color: '#FFFFFF',
              backgroundColor: 'var(--color-primary)',
              textDecoration: 'none',
              transition: 'opacity var(--transition-fast)',
            }}
            className="sl-public-cta-officer"
          >
            Officer Access
          </Link>

          {/* Mobile Menu Toggle Button */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen((prev) => !prev)}
            style={{
              padding: 'var(--space-1) var(--space-2)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border)',
              backgroundColor: 'var(--color-bg-subtle)',
              color: 'var(--color-text-secondary)',
              cursor: 'pointer',
            }}
            className="sl-public-menu-toggle"
            aria-label="Toggle public navigation menu"
          >
            {mobileMenuOpen ? '✕' : '☰'}
          </button>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div
          style={{
            backgroundColor: 'var(--color-bg-header)',
            borderTop: '1px solid var(--color-border)',
            padding: 'var(--space-4)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-3)',
          }}
          className="sl-public-nav-mobile"
        >
          {navLinks.map((link) => (
            <a
              key={link.href}
              href={link.href}
              onClick={() => setMobileMenuOpen(false)}
              style={{
                fontSize: 'var(--font-size-sm)',
                fontWeight: 'var(--font-weight-medium)',
                color: 'var(--color-text-primary)',
                textDecoration: 'none',
                padding: 'var(--space-2) 0',
              }}
            >
              {link.label}
            </a>
          ))}
          <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: 'var(--space-3)', display: 'flex', gap: 'var(--space-2)' }}>
            <Link
              to="/signup?role=bidder"
              onClick={() => setMobileMenuOpen(false)}
              style={{
                flex: 1,
                textAlign: 'center',
                padding: 'var(--space-2)',
                borderRadius: 'var(--radius-sm)',
                fontSize: 'var(--font-size-xs)',
                fontWeight: 'var(--font-weight-semibold)',
                color: 'var(--color-success)',
                backgroundColor: 'var(--color-success-subtle)',
                border: '1px solid var(--color-success)',
                textDecoration: 'none',
              }}
            >
              Bidder Signup
            </Link>
            <Link
              to="/signup?role=officer"
              onClick={() => setMobileMenuOpen(false)}
              style={{
                flex: 1,
                textAlign: 'center',
                padding: 'var(--space-2)',
                borderRadius: 'var(--radius-sm)',
                fontSize: 'var(--font-size-xs)',
                fontWeight: 'var(--font-weight-semibold)',
                color: '#FFFFFF',
                backgroundColor: 'var(--color-primary)',
                textDecoration: 'none',
              }}
            >
              Officer Access
            </Link>
          </div>
        </div>
      )}

      <style>{`
        @media (min-width: 900px) {
          .sl-public-nav-desktop {
            display: flex !important;
          }
          .sl-public-cta-bidder {
            display: inline-block !important;
          }
          .sl-public-cta-officer {
            display: inline-block !important;
          }
          .sl-public-menu-toggle {
            display: none !important;
          }
          .sl-public-nav-mobile {
            display: none !important;
          }
        }
      `}</style>
    </header>
  );
}
