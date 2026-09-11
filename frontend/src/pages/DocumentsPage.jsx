import React from 'react';
import { useNavigate } from 'react-router-dom';
import PageContainer from '../components/layout/PageContainer.jsx';
import Badge from '../components/common/Badge.jsx';
import Button from '../components/common/Button.jsx';
import { DEMO_DOCUMENTS, getBidderById } from '../data/demoData.js';

/**
 * DocumentsPage — M20
 * Central document repository view across all bidders.
 */
export default function DocumentsPage() {
  const navigate = useNavigate();

  const getDocStatusBadge = (status) => {
    switch (status) {
      case 'VERIFIED': return <Badge variant="success">Verified</Badge>;
      case 'UPLOADED': return <Badge variant="info">Uploaded</Badge>;
      case 'PENDING': return <Badge variant="warning">Pending</Badge>;
      case 'REJECTED': return <Badge variant="danger">Rejected</Badge>;
      default: return <Badge variant="neutral">{status}</Badge>;
    }
  };

  const statuses = ['VERIFIED', 'UPLOADED', 'PENDING', 'REJECTED'];

  return (
    <PageContainer
      title="Documents"
      subtitle="Uploaded tender documentation and compliance repository files"
      actions={<Badge variant="info">{DEMO_DOCUMENTS.length} documents</Badge>}
    >
      {/* Summary */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          gap: 'var(--space-3)',
          marginBottom: 'var(--space-4)',
        }}
      >
        {statuses.map((status) => {
          const count = DEMO_DOCUMENTS.filter(d => d.status === status).length;
          const colors = {
            VERIFIED: 'var(--color-success)',
            UPLOADED: 'var(--color-primary)',
            PENDING: 'var(--color-warning)',
            REJECTED: 'var(--color-danger)',
          };
          return (
            <div
              key={status}
              style={{
                backgroundColor: 'var(--color-bg-card)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                padding: 'var(--space-4)',
                boxShadow: 'var(--shadow-xs)',
              }}
            >
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 'var(--space-1)' }}>
                {status.charAt(0) + status.slice(1).toLowerCase()}
              </div>
              <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 'var(--font-weight-bold)', color: colors[status] }}>
                {count}
              </div>
            </div>
          );
        })}
      </div>

      {/* Documents table */}
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
          <h2 style={{ fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-primary)' }}>
            Document Repository
          </h2>
          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
            {DEMO_DOCUMENTS.length} records
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
                <th style={{ padding: 'var(--space-3) var(--space-5)' }}>Document Type</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Vendor</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Filename</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Status</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Verified By</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Uploaded</th>
                <th style={{ padding: 'var(--space-3) var(--space-5)', textAlign: 'right' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {DEMO_DOCUMENTS.map((doc, index) => {
                const bidder = getBidderById(doc.bidderId);
                return (
                  <tr
                    key={doc.id}
                    style={{
                      borderBottom: index === DEMO_DOCUMENTS.length - 1 ? 'none' : '1px solid var(--color-border-subtle)',
                      transition: 'background-color var(--transition-fast)',
                    }}
                    onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'var(--color-bg-hover)'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; }}
                  >
                    <td style={{ padding: 'var(--space-3) var(--space-5)', fontWeight: 'var(--font-weight-medium)', color: 'var(--color-text-primary)' }}>
                      {doc.type}
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-4)', fontSize: 'var(--font-size-xs)' }}>
                      {bidder ? (
                        <button
                          type="button"
                          style={{ background: 'none', border: 'none', color: 'var(--color-primary)', cursor: 'pointer', padding: 0, fontSize: 'var(--font-size-xs)', textAlign: 'left' }}
                          onClick={() => navigate(`/bidders/${doc.bidderId}`)}
                        >
                          {bidder.name}
                        </button>
                      ) : doc.bidderId}
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-4)', fontFamily: 'var(--font-family-mono)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                      {doc.filename}
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                      {getDocStatusBadge(doc.status)}
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-4)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                      {doc.verifiedBy}
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-4)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                      {doc.uploadedDate}
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-5)', textAlign: 'right' }}>
                      <Button
                        variant="ghost"
                        size="sm"
                        style={{ color: 'var(--color-primary)' }}
                        onClick={() => bidder && navigate(`/bidders/${bidder.id}`)}
                      >
                        View Bidder →
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </PageContainer>
  );
}
