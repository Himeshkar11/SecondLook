import React from 'react';
import PageContainer from '../components/layout/PageContainer.jsx';
import Badge from '../components/common/Badge.jsx';
import { DEMO_AUDIT_LOG } from '../data/demoData.js';

/**
 * AuditPage — M20
 * Tamper-evident audit trail of compliance evaluations.
 */
export default function AuditPage() {
  const getEventBadge = (event) => {
    switch (event) {
      case 'VERIFICATION_COMPLETED': return <Badge variant="success">Verification</Badge>;
      case 'VERIFICATION_FLAGGED': return <Badge variant="danger">Flagged</Badge>;
      case 'DOCUMENT_UPLOADED': return <Badge variant="info">Doc Upload</Badge>;
      case 'DOCUMENT_REJECTED': return <Badge variant="danger">Doc Rejected</Badge>;
      case 'TENDER_PUBLISHED': return <Badge variant="neutral">Tender</Badge>;
      case 'OFFICER_DECISION': return <Badge variant="warning">Officer Action</Badge>;
      default: return <Badge variant="neutral">{event}</Badge>;
    }
  };

  return (
    <PageContainer
      title="Audit Log"
      subtitle="Tamper-evident audit trail of compliance evaluations and system events"
      actions={<Badge variant="info">{DEMO_AUDIT_LOG.length} events</Badge>}
    >
      <div
        style={{
          backgroundColor: 'var(--color-bg-card)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--color-border)',
          boxShadow: 'var(--shadow-xs)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            padding: 'var(--space-4) var(--space-5)',
            borderBottom: '1px solid var(--color-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <h2 style={{ fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-primary)' }}>
              System Event Log
            </h2>
            <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
              All verification, document, and officer events — demo data only
            </p>
          </div>
          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', fontFamily: 'var(--font-family-mono)' }}>
            Demo Portal · Read-only
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', fontSize: 'var(--font-size-sm)' }}>
            <thead>
              <tr
                style={{
                  backgroundColor: 'var(--color-bg-subtle)',
                  borderBottom: '1px solid var(--color-border)',
                  fontSize: 'var(--font-size-xs)',
                  color: 'var(--color-text-muted)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                }}
              >
                <th style={{ padding: 'var(--space-3) var(--space-5)' }}>Event ID</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Type</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Entity</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Actor</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Details</th>
                <th style={{ padding: 'var(--space-3) var(--space-5)', textAlign: 'right' }}>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {DEMO_AUDIT_LOG.map((entry, index) => (
                <tr
                  key={entry.id}
                  style={{
                    borderBottom: index === DEMO_AUDIT_LOG.length - 1 ? 'none' : '1px solid var(--color-border-subtle)',
                    transition: 'background-color var(--transition-fast)',
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'var(--color-bg-hover)'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; }}
                >
                  <td style={{ padding: 'var(--space-3) var(--space-5)', fontFamily: 'var(--font-family-mono)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                    {entry.id}
                  </td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                    {getEventBadge(entry.event)}
                  </td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-primary)', fontWeight: 'var(--font-weight-medium)' }}>
                    {entry.entity}
                  </td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                    {entry.actor}
                  </td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)', maxWidth: '260px' }}>
                    {entry.details}
                  </td>
                  <td style={{ padding: 'var(--space-3) var(--space-5)', textAlign: 'right', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', whiteSpace: 'nowrap' }}>
                    {entry.timestamp}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Info note */}
      <div
        style={{
          backgroundColor: 'var(--color-bg-card)',
          border: '1px solid var(--color-border)',
          borderLeft: '4px solid var(--color-info)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-4)',
          fontSize: 'var(--font-size-xs)',
          color: 'var(--color-text-secondary)',
        }}
      >
        <strong style={{ color: 'var(--color-text-primary)' }}>Note:</strong> In the production system, this audit log will be cryptographically signed and immutable. All officer actions, pipeline outputs, and document events will be recorded here with full attribution. Authentication and RBAC are deferred to a future milestone.
      </div>
    </PageContainer>
  );
}
