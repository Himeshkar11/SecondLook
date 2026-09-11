import React from 'react';
import Badge from '../common/Badge.jsx';

/**
 * Reusable StatCard component
 * Displays high-level metrics with enterprise context
 */
export default function StatCard({
  title,
  value,
  context,
  badgeText,
  badgeVariant = 'neutral',
  icon,
}) {
  return (
    <div
      style={{
        backgroundColor: 'var(--color-bg-card)',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--color-border)',
        padding: 'var(--space-4) var(--space-5)',
        boxShadow: 'var(--shadow-xs)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-2)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span
          style={{
            fontSize: 'var(--font-size-xs)',
            fontWeight: 'var(--font-weight-semibold)',
            color: 'var(--color-text-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
          }}
        >
          {title}
        </span>
        {icon && <span style={{ fontSize: '18px' }}>{icon}</span>}
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: 'var(--space-3)' }}>
        <span
          style={{
            fontSize: 'var(--font-size-2xl)',
            fontWeight: 'var(--font-weight-bold)',
            color: 'var(--color-text-primary)',
            lineHeight: 1.1,
          }}
        >
          {value}
        </span>
        {badgeText && (
          <Badge variant={badgeVariant}>{badgeText}</Badge>
        )}
      </div>

      {context && (
        <div
          style={{
            fontSize: 'var(--font-size-xs)',
            color: 'var(--color-text-secondary)',
            marginTop: '2px',
          }}
        >
          {context}
        </div>
      )}
    </div>
  );
}
