import React from 'react';

/**
 * Standardized PageContainer component
 * Enforces consistent max-width, responsive padding, and vertical rhythm across pages.
 */
export default function PageContainer({
  title,
  subtitle,
  actions,
  children,
  maxWidth = 'var(--max-content-width)',
}) {
  return (
    <div
      style={{
        flex: 1,
        width: '100%',
        maxWidth,
        margin: '0 auto',
        padding: 'var(--space-6) var(--space-6)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-6)',
      }}
      className="sl-page-container"
    >
      {(title || actions) && (
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: 'var(--space-4)',
            borderBottom: '1px solid var(--color-border)',
            paddingBottom: 'var(--space-4)',
          }}
        >
          <div>
            {title && (
              <h1
                style={{
                  fontSize: 'var(--font-size-2xl)',
                  fontWeight: 'var(--font-weight-bold)',
                  color: 'var(--color-text-primary)',
                  letterSpacing: '-0.01em',
                }}
              >
                {title}
              </h1>
            )}
            {subtitle && (
              <p
                style={{
                  fontSize: 'var(--font-size-sm)',
                  color: 'var(--color-text-muted)',
                  marginTop: 'var(--space-1)',
                }}
              >
                {subtitle}
              </p>
            )}
          </div>
          {actions && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              {actions}
            </div>
          )}
        </div>
      )}

      <div>{children}</div>
    </div>
  );
}
