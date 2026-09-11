import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import PageContainer from '../components/layout/PageContainer.jsx';
import Badge from '../components/common/Badge.jsx';
import Button from '../components/common/Button.jsx';
import EmptyState from '../components/common/EmptyState.jsx';
import { getTenderById, getBiddersByTender } from '../data/demoData.js';

/**
 * TenderDetailPage — M20
 * Single tender detail view with bidder list and navigation into bidder verification.
 */
export default function TenderDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const tenderId = decodeURIComponent(id);
  const tender = getTenderById(tenderId);
  const bidders = tender ? getBiddersByTender(tenderId) : [];

  if (!tender) {
    return (
      <PageContainer title="Tender Not Found">
        <EmptyState
          title="Tender not found"
          description="The tender reference could not be located in the demo dataset."
          actionLabel="Back to Tenders"
          onAction={() => navigate('/tenders')}
        />
      </PageContainer>
    );
  }

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

  const getBidderStatusBadge = (status) => {
    switch (status) {
      case 'VERIFIED': return <Badge variant="success">Verified</Badge>;
      case 'PENDING': return <Badge variant="info">Pending</Badge>;
      case 'FLAGGED': return <Badge variant="danger">Flagged</Badge>;
      default: return <Badge variant="neutral">{status}</Badge>;
    }
  };

  return (
    <PageContainer
      title={tender.id}
      subtitle={tender.title}
      actions={
        <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
          <Button variant="secondary" size="sm" onClick={() => navigate('/tenders')}>
            ← Back to Tenders
          </Button>
          <Button variant="primary" size="sm" onClick={() => navigate('/verification')}>
            Run Verification
          </Button>
        </div>
      }
    >
      {/* Tender metadata card */}
      <div
        style={{
          backgroundColor: 'var(--color-bg-card)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-5)',
          boxShadow: 'var(--shadow-xs)',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: 'var(--space-4)',
            flexWrap: 'wrap',
            gap: 'var(--space-3)',
          }}
        >
          <h2 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-primary)' }}>
            Tender Details
          </h2>
          <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
            {getStatusBadge(tender.status)}
            {getRiskBadge(tender.risk)}
          </div>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: 'var(--space-4)',
          }}
        >
          {[
            { label: 'Procuring Organisation', value: tender.organization },
            { label: 'Department', value: tender.department },
            { label: 'Category', value: tender.category },
            { label: 'Estimated Value', value: tender.value },
            { label: 'Published Date', value: tender.publishedDate },
            { label: 'Closing Date', value: tender.closingDate },
            { label: 'Total Bids Received', value: tender.bids },
          ].map((field) => (
            <div key={field.label}>
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '2px' }}>
                {field.label}
              </div>
              <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)', fontWeight: 'var(--font-weight-medium)' }}>
                {field.value}
              </div>
            </div>
          ))}
        </div>

        <div style={{ marginTop: 'var(--space-4)', paddingTop: 'var(--space-4)', borderTop: '1px solid var(--color-border-subtle)' }}>
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 'var(--space-2)' }}>
            Scope of Work
          </div>
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
            {tender.description}
          </p>
        </div>
      </div>

      {/* Bidders table */}
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
            <h3 style={{ fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-primary)' }}>
              Submitted Bidders
            </h3>
            <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
              Bidders whose compliance documentation has been received
            </p>
          </div>
          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
            {bidders.length} of {tender.bids} shown
          </span>
        </div>

        {bidders.length === 0 ? (
          <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>
            No bidder details available in demo dataset for this tender.
          </div>
        ) : (
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
                  <th style={{ padding: 'var(--space-3) var(--space-5)' }}>Bidder Name</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)' }}>PAN</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)' }}>GSTIN</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'center' }}>Compliance</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Risk</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Status</th>
                  <th style={{ padding: 'var(--space-3) var(--space-5)', textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {bidders.map((bidder, index) => (
                  <tr
                    key={bidder.id}
                    style={{
                      borderBottom: index === bidders.length - 1 ? 'none' : '1px solid var(--color-border-subtle)',
                      cursor: 'pointer',
                      transition: 'background-color var(--transition-fast)',
                    }}
                    onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'var(--color-bg-hover)'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; }}
                    onClick={() => navigate(`/bidders/${bidder.id}`)}
                  >
                    <td style={{ padding: 'var(--space-3) var(--space-5)' }}>
                      <div style={{ fontWeight: 'var(--font-weight-medium)', color: 'var(--color-text-primary)' }}>
                        {bidder.name}
                      </div>
                      {bidder.msmeCategory !== 'NOT APPLICABLE' && (
                        <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: '2px' }}>
                          MSME: {bidder.msmeCategory}
                        </div>
                      )}
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-4)', fontFamily: 'var(--font-family-mono)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                      {bidder.pan}
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-4)', fontFamily: 'var(--font-family-mono)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                      {bidder.gstin}
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'center' }}>
                      <span
                        style={{
                          fontWeight: 'var(--font-weight-bold)',
                          color: bidder.compliance >= 90 ? 'var(--color-success)' : bidder.compliance >= 70 ? 'var(--color-warning)' : 'var(--color-danger)',
                        }}
                      >
                        {bidder.compliance}%
                      </span>
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                      {getRiskBadge(bidder.risk)}
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                      {getBidderStatusBadge(bidder.status)}
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-5)', textAlign: 'right' }}>
                      <Button
                        variant="ghost"
                        size="sm"
                        style={{ color: 'var(--color-primary)' }}
                        onClick={(e) => { e.stopPropagation(); navigate(`/bidders/${bidder.id}`); }}
                      >
                        Review →
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </PageContainer>
  );
}
