import React from 'react';
import Badge from '../common/Badge.jsx';

/**
 * Reusable ComplianceCard component
 * Displays overall compliance percentage and categorical breakdown
 */
export default function ComplianceCard({
  overallRate = 82,
  breakdown = [
    { label: 'GST Validations', rate: 92 },
    { label: 'PAN Registrations', rate: 96 },
    { label: 'MSME / Udyam', rate: 78 },
    { label: 'EPFO / ESIC', rate: 64 },
  ],
}) {
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
            Compliance Overview
          </h3>
          <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
            Statutory registry verification rate
          </p>
        </div>
        <Badge variant="success">Compliant</Badge>
      </div>

      {/* Main Metric Bar */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 'var(--space-1)' }}>
          <span style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--gov-green)' }}>
            {overallRate}%
          </span>
          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
            Threshold: 75% min
          </span>
        </div>

        <div
          role="progressbar"
          aria-valuenow={overallRate}
          aria-valuemin={0}
          aria-valuemax={100}
          style={{
            height: '8px',
            borderRadius: 'var(--radius-full)',
            backgroundColor: 'var(--color-bg-subtle)',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              width: `${overallRate}%`,
              height: '100%',
              backgroundColor: 'var(--gov-green)',
              borderRadius: 'var(--radius-full)',
              transition: 'width 0.3s ease',
            }}
          />
        </div>
      </div>

      {/* Categorical Breakdown */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)', borderTop: '1px solid var(--color-border-subtle)', paddingTop: 'var(--space-3)' }}>
        {breakdown.map((item) => (
          <div key={item.label} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 'var(--font-size-xs)' }}>
            <span style={{ color: 'var(--color-text-secondary)' }}>{item.label}</span>
            <span style={{ fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-primary)' }}>
              {item.rate}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
