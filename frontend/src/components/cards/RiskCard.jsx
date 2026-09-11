import React from 'react';
import Badge from '../common/Badge.jsx';

/**
 * Reusable RiskCard component
 * Displays high-level risk assessment and risk factor indicators
 */
export default function RiskCard({
  riskLevel = 'LOW',
  score = 88,
  factors = [
    { name: 'Blacklist Registry Check', status: 'CLEAR', safe: true },
    { name: 'Debarment Index', status: 'CLEAR', safe: true },
    { name: 'Document Authenticity', status: 'CONFIRMED', safe: true },
  ],
}) {
  const badgeVariant = riskLevel === 'LOW' ? 'success' : riskLevel === 'MEDIUM' ? 'warning' : 'danger';

  return (
    <div
      style={{
        backgroundColor: 'var(--color-bg-card)',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--color-border)',
        padding: 'var(--space-5)',
        boxShadow: 'var(--shadow-xs)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-4)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h3
            style={{
              fontSize: 'var(--font-size-base)',
              fontWeight: 'var(--font-weight-semibold)',
              color: 'var(--color-text-primary)',
            }}
          >
            Risk Assessment
          </h3>
          <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
            Systemic bidder risk index
          </p>
        </div>
        <Badge variant={badgeVariant}>{riskLevel} RISK</Badge>
      </div>

      <div
        style={{
          display: 'flex',
          alignItems: 'baseline',
          justifyContent: 'space-between',
          backgroundColor: 'var(--color-bg-subtle)',
          padding: 'var(--space-3) var(--space-4)',
          borderRadius: 'var(--radius-sm)',
        }}
      >
        <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
          Composite Confidence Score
        </span>
        <span style={{ fontSize: 'var(--font-size-xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-primary)' }}>
          {score}/100
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
        <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
          Key Factors
        </div>
        {factors.map((factor) => (
          <div
            key={factor.name}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              fontSize: 'var(--font-size-xs)',
            }}
          >
            <span style={{ color: 'var(--color-text-secondary)' }}>{factor.name}</span>
            <Badge variant={factor.safe ? 'success' : 'danger'}>{factor.status}</Badge>
          </div>
        ))}
      </div>
    </div>
  );
}
