import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import PageContainer from '../components/layout/PageContainer.jsx';
import Badge from '../components/common/Badge.jsx';
import Button from '../components/common/Button.jsx';
import Loading from '../components/common/Loading.jsx';
import EmptyState from '../components/common/EmptyState.jsx';
import { getBidders } from '../services/bidderService.js';

/**
 * BiddersPage — Dynamic Supabase-backed vendor registry module.
 * Lists bidders fetched from the backend API with loading, empty, and error handling.
 */
export default function BiddersPage() {
  const navigate = useNavigate();
  const [bidders, setBidders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchBidders = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getBidders();
      setBidders(data.items || []);
    } catch (err) {
      setError(err.message || 'Unable to load bidders. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBidders();
  }, [fetchBidders]);

  const getRiskBadge = (risk) => {
    switch ((risk || 'LOW').toUpperCase()) {
      case 'LOW': return <Badge variant="success">Low Risk</Badge>;
      case 'MEDIUM': return <Badge variant="warning">Med Risk</Badge>;
      case 'HIGH': return <Badge variant="danger">High Risk</Badge>;
      default: return <Badge variant="neutral">{risk}</Badge>;
    }
  };

  const getStatusBadge = (status) => {
    switch ((status || '').toUpperCase()) {
      case 'VERIFIED': return <Badge variant="success">Verified</Badge>;
      case 'PENDING': return <Badge variant="info">Pending</Badge>;
      case 'FLAGGED': return <Badge variant="danger">Flagged</Badge>;
      default: return <Badge variant="neutral">{status}</Badge>;
    }
  };

  const avgCompliance = bidders.length > 0
    ? Math.round(bidders.reduce((s, b) => s + (Number(b.compliance) || 0), 0) / bidders.length)
    : 0;

  return (
    <PageContainer
      title="Bidders"
      subtitle="Registry of prospective vendors and their statutory compliance status"
      actions={<Badge variant="info">{bidders.length} vendors</Badge>}
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
          { label: 'Verified', count: bidders.filter(b => (b.status || '').toUpperCase() === 'VERIFIED').length, color: 'var(--color-success)' },
          { label: 'Pending', count: bidders.filter(b => (b.status || '').toUpperCase() === 'PENDING').length, color: 'var(--color-warning)' },
          { label: 'Flagged', count: bidders.filter(b => (b.status || '').toUpperCase() === 'FLAGGED').length, color: 'var(--color-danger)' },
          { label: 'Avg. Compliance', count: bidders.length > 0 ? `${avgCompliance}%` : '—', color: 'var(--color-primary)' },
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
            <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 'var(--font-weight-bold)', color: s.color }}>{s.count}</div>
          </div>
        ))}
      </div>

      {/* Main Content Area */}
      {loading ? (
        <div
          style={{
            backgroundColor: 'var(--color-bg-card)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--color-border)',
            padding: 'var(--space-8)',
          }}
        >
          <Loading message="Loading bidders registry..." />
        </div>
      ) : error ? (
        <EmptyState
          title="Unable to load bidders"
          description={error}
          actionLabel="Retry"
          onAction={fetchBidders}
        />
      ) : bidders.length === 0 ? (
        <EmptyState
          title="No bidders found."
          description="There are currently no registered vendors in the compliance database."
        />
      ) : (
        /* Bidders table */
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
              All Vendors
            </h2>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
              {bidders.length} records
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
                  <th style={{ padding: 'var(--space-3) var(--space-5)' }}>Vendor Name</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)' }}>PAN</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Tender</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'center' }}>Compliance</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Risk</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Status</th>
                  <th style={{ padding: 'var(--space-3) var(--space-5)', textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {bidders.map((bidder, index) => {
                  const tenderRef = bidder.tenderId || bidder.tender_reference || 'N/A';
                  return (
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
                            MSME — {bidder.msmeCategory}
                          </div>
                        )}
                      </td>
                      <td style={{ padding: 'var(--space-3) var(--space-4)', fontFamily: 'var(--font-family-mono)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                        {bidder.pan || bidder.pan_number || 'N/A'}
                      </td>
                      <td style={{ padding: 'var(--space-3) var(--space-4)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                        <button
                          type="button"
                          style={{
                            background: 'none',
                            border: 'none',
                            color: tenderRef !== 'N/A' ? 'var(--color-primary)' : 'var(--color-text-muted)',
                            cursor: tenderRef !== 'N/A' ? 'pointer' : 'default',
                            padding: 0,
                            fontFamily: 'var(--font-family-mono)',
                            fontSize: 'var(--font-size-xs)',
                            textAlign: 'left',
                          }}
                          onClick={(e) => {
                            e.stopPropagation();
                            if (tenderRef !== 'N/A') {
                              navigate(`/tenders/${encodeURIComponent(tenderRef)}`);
                            }
                          }}
                        >
                          {tenderRef}
                        </button>
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
                        {getStatusBadge(bidder.status)}
                      </td>
                      <td style={{ padding: 'var(--space-3) var(--space-5)', textAlign: 'right' }}>
                        <Button
                          variant="ghost"
                          size="sm"
                          style={{ color: 'var(--color-primary)' }}
                          onClick={(e) => { e.stopPropagation(); navigate(`/bidders/${bidder.id}`); }}
                        >
                          View →
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </PageContainer>
  );
}
