import React from 'react';

/**
 * Reusable Loading indicator
 */
export default function Loading({ message = 'Loading...', size = 'md' }) {
  const spinnerSize = size === 'sm' ? '16px' : size === 'lg' ? '32px' : '24px';

  return (
    <div
      role="status"
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 'var(--space-3)',
        padding: 'var(--space-6)',
        color: 'var(--color-text-secondary)',
        fontSize: 'var(--font-size-sm)',
      }}
    >
      <div
        style={{
          width: spinnerSize,
          height: spinnerSize,
          borderRadius: 'var(--radius-full)',
          border: '2px solid var(--color-border)',
          borderTopColor: 'var(--color-primary)',
          animation: 'sl-spin 0.8s linear infinite',
        }}
      />
      <span>{message}</span>
      <style>{`
        @keyframes sl-spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
