import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import PageContainer from '../components/layout/PageContainer.jsx';
import Badge from '../components/common/Badge.jsx';
import Button from '../components/common/Button.jsx';
import Loading from '../components/common/Loading.jsx';
import EmptyState from '../components/common/EmptyState.jsx';
import { getTenders } from '../services/tenderService.js';

/**
 * TendersPage — Dynamic Supabase-backed procurement tenders module.
 * Lists active tenders fetched from the backend API with loading, empty, and error handling.
 */
export default function TendersPage() {
  const navigate = useNavigate();
  const [tenders, setTenders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchTenders = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getTenders();
      setTenders(data.items || []);
    } catch (err) {
      setError(err.message || 'Unable to load tenders. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTenders();
  }, [fetchTenders]);

  const getStatusBadge = (status) => {
    const s = (status || '').toUpperCase();
    switch (s) {
      case 'ACTIVE':
        return <Badge variant="success">Active</Badge>;
      case 'REVIEW':
      case 'UNDER_REVIEW':
        return <Badge variant="warning">Under Review</Badge>;
      case 'PENDING':
      case 'DRAFT':
        return <Badge variant="info">Pending</Badge>;
      case 'CLOSED':
        return <Badge variant="neutral">Closed</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };

  const getRiskBadge = (risk) => {
    const r = (risk || 'LOW').toUpperCase();
    switch (r) {
      case 'LOW':
        return <Badge variant="success">Low Risk</Badge>;
      case 'MEDIUM':
      case 'MED':
        return <Badge variant="warning">Med Risk</Badge>;
      case 'HIGH':
        return <Badge variant="danger">High Risk</Badge>;
      default:
        return <Badge variant="neutral">{risk}</Badge>;
    }
  };

  return (
    <PageContainer
      title="Tenders"
      subtitle="Active GeM procurement tenders under compliance oversight"
      actions={
        <Badge variant="info">{tenders.length} tenders</Badge>
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
          { label: 'Active', count: tenders.filter(t => (t.status || '').toUpperCase() === 'ACTIVE').length, variant: 'success' },
          { label: 'Under Review', count: tenders.filter(t => ['REVIEW', 'UNDER_REVIEW'].includes((t.status || '').toUpperCase())).length, variant: 'warning' },
          { label: 'Pending', count: tenders.filter(t => ['PENDING', 'DRAFT'].includes((t.status || '').toUpperCase())).length, variant: 'info' },
          { label: 'Total Bids', count: tenders.reduce((s, t) => s + (Number(t.bids) || 0), 0), variant: 'neutral' },
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
          <Loading message="Loading tenders from compliance database..." />
        </div>
      ) : error ? (
        <EmptyState
          title="Unable to load tenders"
          description={error}
          actionLabel="Retry"
          onAction={fetchTenders}
        />
      ) : tenders.length === 0 ? (
        <EmptyState
          title="No tenders found."
          description="There are currently no active procurement tenders under compliance oversight in the database."
        />
      ) : (
        /* Tenders table */
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
              Showing {tenders.length} items
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
                {tenders.map((tender, index) => {
                  const tenderRef = tender.reference_number || tender.id;
                  return (
                    <tr
                      key={tender.id}
                      style={{
                        borderBottom: index === tenders.length - 1 ? 'none' : '1px solid var(--color-border-subtle)',
                        cursor: 'pointer',
                        transition: 'background-color var(--transition-fast)',
                      }}
                      onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'var(--color-bg-hover)'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; }}
                      onClick={() => navigate(`/tenders/${encodeURIComponent(tenderRef)}`)}
                    >
                      <td style={{ padding: 'var(--space-3) var(--space-5)' }}>
                        <div style={{ fontWeight: 'var(--font-weight-medium)', color: 'var(--color-primary)', fontFamily: 'var(--font-family-mono)', fontSize: 'var(--font-size-xs)' }}>
                          {tenderRef}
                        </div>
                        <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: '2px', maxWidth: '280px' }}>
                          {tender.title}
                        </div>
                      </td>
                      <td style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-xs)' }}>
                        {tender.organization || 'CPCL / Ministry of Petroleum'}
                      </td>
                      <td style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--color-text-primary)', fontWeight: 'var(--font-weight-medium)', whiteSpace: 'nowrap', fontSize: 'var(--font-size-xs)' }}>
                        {tender.value || '₹ 4,20,00,000'}
                      </td>
                      <td style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'center', fontWeight: 'var(--font-weight-semibold)' }}>
                        {tender.bids ?? 0}
                      </td>
                      <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                        {getStatusBadge(tender.status)}
                      </td>
                      <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                        {getRiskBadge(tender.risk || 'LOW')}
                      </td>
                      <td style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-xs)', whiteSpace: 'nowrap' }}>
                        {tender.closingDate || '—'}
                      </td>
                      <td style={{ padding: 'var(--space-3) var(--space-5)', textAlign: 'right' }}>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => { e.stopPropagation(); navigate(`/tenders/${encodeURIComponent(tenderRef)}`); }}
                          style={{ color: 'var(--color-primary)' }}
                        >
                          View Details →
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
