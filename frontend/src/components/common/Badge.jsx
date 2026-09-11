import React from 'react';

/**
 * Reusable Badge component
 * Semantic variants: success, warning, danger, info, neutral
 */
export default function Badge({
  children,
  variant = 'neutral',
  className = '',
}) {
  const baseStyles = {
    display: 'inline-flex',
    alignItems: 'center',
    padding: '2px 8px',
    borderRadius: 'var(--radius-sm)',
    fontSize: 'var(--font-size-xs)',
    fontWeight: 'var(--font-weight-semibold)',
    lineHeight: 1.4,
    border: '1px solid transparent',
    letterSpacing: '0.02em',
  };

  const variants = {
    success: {
      backgroundColor: 'var(--color-success-subtle)',
      color: 'var(--color-success)',
      borderColor: '#B8E2B5',
    },
    warning: {
      backgroundColor: 'var(--color-warning-subtle)',
      color: '#B45309',
      borderColor: '#FDE68A',
    },
    danger: {
      backgroundColor: 'var(--color-danger-subtle)',
      color: 'var(--color-danger)',
      borderColor: '#FCA5A5',
    },
    info: {
      backgroundColor: 'var(--color-info-subtle)',
      color: 'var(--color-info)',
      borderColor: '#BAE6FD',
    },
    neutral: {
      backgroundColor: 'var(--color-bg-subtle)',
      color: 'var(--color-text-secondary)',
      borderColor: 'var(--color-border)',
    },
  };

  return (
    <span
      style={{
        ...baseStyles,
        ...variants[variant],
      }}
      className={`sl-badge ${className}`}
    >
      {children}
    </span>
  );
}
