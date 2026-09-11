import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import PageContainer from '../components/layout/PageContainer.jsx';
import Badge from '../components/common/Badge.jsx';
import Button from '../components/common/Button.jsx';
import Loading from '../components/common/Loading.jsx';
import EmptyState from '../components/common/EmptyState.jsx';
import { getTenderById, getTenderBidders } from '../services/tenderService.js';

/**
 * TenderDetailPage — Dynamic Supabase-backed tender detail view.
 * Loads tender details and associated bidders from the backend API using the
 * tender ID/reference from the URL. Works when loaded directly via URL.
 */
export default function TenderDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const tenderId = decodeURIComponent(id);

  const [tender, setTender] = useState(null);
  const [bidders, setBidders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notFound, setNotFound] = useState(false);
  const [biddersLoading, setBiddersLoading] = useState(false);

  const fetchTenderDetails = useCallback(async () => {
    setLoading(true);
    setError(null);
    setNotFound(false);
    setTender(null);
    setBidders([]);

    try {
      const data = await getTenderById(tenderId);
      setTender(data);

      // Now fetch associated bidders
      setBiddersLoading(true);
      try {
        const bidderData = await getTenderBidders(tenderId);
        setBidders(bidderData.items || []);
      } catch {
        // Bidders failing is non-fatal; show empty list
        setBidders([]);
      } finally {
        setBiddersLoading(false);
      }
    } catch (err) {
      if (err.status === 404) {
        setNotFound(true);
      } else {
        setError(err.message || 'Unable to load tender details. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  }, [tenderId]);

  useEffect(() => {
    fetchTenderDetails();
  }, [fetchTenderDetails]);

  const getStatusBadge = (status) => {
    const s = (status || '').toUpperCase();
    switch (s) {
      case 'ACTIVE': return <Badge variant="success">Active</Badge>;
      case 'REVIEW':
      case 'UNDER_REVIEW': return <Badge variant="warning">Under Review</Badge>;
      case 'PENDING':
      case 'DRAFT': return <Badge variant="info">Pending</Badge>;
      case 'CLOSED': return <Badge variant="neutral">Closed</Badge>;
      default: return <Badge variant="neutral">{status}</Badge>;
    }
  };

  const getRiskBadge = (risk) => {
    switch ((risk || 'LOW').toUpperCase()) {
      case 'LOW': return <Badge variant="success">Low Risk</Badge>;
      case 'MEDIUM': return <Badge variant="warning">Med Risk</Badge>;
      case 'HIGH': return <Badge variant="danger">High Risk</Badge>;
      default: return <Badge variant="neutral">{risk}</Badge>;
    }
  };

  const getBidderStatusBadge = (status) => {
    switch ((status || '').toUpperCase()) {
      case 'VERIFIED': return <Badge variant="success">Verified</Badge>;
      case 'PENDING': return <Badge variant="info">Pending</Badge>;
      case 'FLAGGED': return <Badge variant="danger">Flagged</Badge>;
      default: return <Badge variant="neutral">{status}</Badge>;
    }
  };

  // ─── Loading state ───────────────────────────────────────────────────────────
  if (loading) {
    return (
      <PageContainer title="Tender Details">
        <div
          style={{
            backgroundColor: 'var(--color-bg-card)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--color-border)',
            padding: 'var(--space-8)',
          }}
        >
          <Loading message="Loading tender details..." />
        </div>
      </PageContainer>
    );
  }

  // ─── Not found state ─────────────────────────────────────────────────────────
  if (notFound) {
    return (
      <PageContainer title="Tender Not Found">
        <EmptyState
          title="Tender not found"
          description="The requested tender could not be found in the database."
          actionLabel="Back to Tenders"
          onAction={() => navigate('/tenders')}
        />
      </PageContainer>
    );
  }

  // ─── Error state ─────────────────────────────────────────────────────────────
  if (error) {
    return (
      <PageContainer title="Tender Details">
        <EmptyState
          title="Unable to load tender details"
          description={error}
          actionLabel="Retry"
          onAction={fetchTenderDetails}
        />
      </PageContainer>
    );
  }

  const tenderRef = tender.reference_number || tender.id;

  return (
    <PageContainer
      title={tenderRef}
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
            { label: 'Procuring Organisation', value: tender.organization || '—' },
            { label: 'Department', value: tender.department || '—' },
            { label: 'Category', value: tender.category || '—' },
            { label: 'Estimated Value', value: tender.value || '—' },
            { label: 'Published Date', value: tender.publishedDate || tender.created_at?.slice(0, 10) || '—' },
            { label: 'Closing Date', value: tender.closingDate || '—' },
            { label: 'Total Bids Received', value: tender.bids ?? bidders.length },
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
            {tender.description || 'No description available.'}
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
            {biddersLoading ? '…' : `${bidders.length} shown`}
          </span>
        </div>

        {biddersLoading ? (
          <div style={{ padding: 'var(--space-6)' }}>
            <Loading message="Loading bidders..." size="sm" />
          </div>
        ) : bidders.length === 0 ? (
          <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>
            No bidders have been associated with this tender.
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
                        {bidder.name || bidder.legal_name}
                      </div>
                      {bidder.msmeCategory && bidder.msmeCategory !== 'NOT APPLICABLE' && (
                        <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: '2px' }}>
                          MSME: {bidder.msmeCategory}
                        </div>
                      )}
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-4)', fontFamily: 'var(--font-family-mono)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                      {bidder.pan || bidder.pan_number || 'N/A'}
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-4)', fontFamily: 'var(--font-family-mono)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                      {bidder.gstin || bidder.gst_number || 'N/A'}
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'center' }}>
                      <span
                        style={{
                          fontWeight: 'var(--font-weight-bold)',
                          color: bidder.compliance >= 90 ? 'var(--color-success)' : bidder.compliance >= 70 ? 'var(--color-warning)' : 'var(--color-danger)',
                        }}
                      >
                        {bidder.compliance != null ? `${bidder.compliance}%` : '—'}
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
