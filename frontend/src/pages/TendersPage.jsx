import React from 'react';
import { useNavigate } from 'react-router-dom';
import PageContainer from '../components/layout/PageContainer.jsx';
import Badge from '../components/common/Badge.jsx';
import Button from '../components/common/Button.jsx';
import { DEMO_TENDERS } from '../data/demoData.js';

/**
 * TendersPage — M20
 * Full tender list with navigation into individual tender details.
 */
export default function TendersPage() {
  const navigate = useNavigate();

  const getStatusBadge = (status) => {
    switch (status) {
      case 'ACTIVE': return <Badge variant="success">Active</Badge>;
      case 'REVIEW': return <Badge variant="warning">Under Review</Badge>;
      case 'PENDING': return <Badge variant="info">Pending</Badge>;
      default: return <Badge variant="neutral">{status}</Badge>;
    }
  };

  const getRiskBadge = (risk) => {
    switch (risk) {
      case 'LOW': return <Badge variant="success">Low Risk</Badge>;
      case 'MEDIUM': return <Badge variant="warning">Med Risk</Badge>;
      case 'HIGH': return <Badge variant="danger">High Risk</Badge>;
      default: return <Badge variant="neutral">{risk}</Badge>;
    }
  };

  return (
    <PageContainer
      title="Tenders"
      subtitle="Active GeM procurement tenders under compliance oversight"
      actions={
        <Badge variant="info">{DEMO_TENDERS.length} tenders</Badge>
      }
    >
      {/* Summary stat row */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
          gap: 'var(--space-3)',
          marginBottom: 'var(--space-4)',
        }}
      >
        {[
          { label: 'Active', count: DEMO_TENDERS.filter(t => t.status === 'ACTIVE').length, variant: 'success' },
          { label: 'Under Review', count: DEMO_TENDERS.filter(t => t.status === 'REVIEW').length, variant: 'warning' },
          { label: 'Pending', count: DEMO_TENDERS.filter(t => t.status === 'PENDING').length, variant: 'info' },
          { label: 'Total Bids', count: DEMO_TENDERS.reduce((s, t) => s + t.bids, 0), variant: 'neutral' },
        ].map((s) => (
          <div
            key={s.label}
            style={{
              backgroundColor: 'var(--color-bg-card)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-4)',
              boxShadow: 'var(--shadow-xs)',
            }}
          >
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 'var(--space-1)' }}>{s.label}</div>
            <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)' }}>{s.count}</div>
          </div>
        ))}
      </div>

      {/* Tenders table */}
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
            All Tenders
          </h2>
          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
            Showing {DEMO_TENDERS.length} items
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
                <th style={{ padding: 'var(--space-3) var(--space-5)', whiteSpace: 'nowrap' }}>Tender Reference</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Organisation</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)', whiteSpace: 'nowrap' }}>Est. Value</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'center' }}>Bids</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Status</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Risk</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)', whiteSpace: 'nowrap' }}>Closing Date</th>
                <th style={{ padding: 'var(--space-3) var(--space-5)', textAlign: 'right' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {DEMO_TENDERS.map((tender, index) => (
                <tr
                  key={tender.id}
                  style={{
                    borderBottom: index === DEMO_TENDERS.length - 1 ? 'none' : '1px solid var(--color-border-subtle)',
                    cursor: 'pointer',
                    transition: 'background-color var(--transition-fast)',
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'var(--color-bg-hover)'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; }}
                  onClick={() => navigate(`/tenders/${encodeURIComponent(tender.id)}`)}
                >
                  <td style={{ padding: 'var(--space-3) var(--space-5)' }}>
                    <div style={{ fontWeight: 'var(--font-weight-medium)', color: 'var(--color-primary)', fontFamily: 'var(--font-family-mono)', fontSize: 'var(--font-size-xs)' }}>
                      {tender.id}
                    </div>
                    <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: '2px', maxWidth: '280px' }}>
                      {tender.title}
                    </div>
                  </td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-xs)' }}>
                    {tender.organization}
                  </td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--color-text-primary)', fontWeight: 'var(--font-weight-medium)', whiteSpace: 'nowrap', fontSize: 'var(--font-size-xs)' }}>
                    {tender.value}
                  </td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'center', fontWeight: 'var(--font-weight-semibold)' }}>
                    {tender.bids}
                  </td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                    {getStatusBadge(tender.status)}
                  </td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                    {getRiskBadge(tender.risk)}
                  </td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-xs)', whiteSpace: 'nowrap' }}>
                    {tender.closingDate}
                  </td>
                  <td style={{ padding: 'var(--space-3) var(--space-5)', textAlign: 'right' }}>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => { e.stopPropagation(); navigate(`/tenders/${encodeURIComponent(tender.id)}`); }}
                      style={{ color: 'var(--color-primary)' }}
                    >
                      View Details →
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </PageContainer>
  );
}
