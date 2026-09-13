import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import PageContainer from '../../components/layout/PageContainer.jsx';
import Badge from '../../components/common/Badge.jsx';
import Button from '../../components/common/Button.jsx';
import Loading from '../../components/common/Loading.jsx';
import EmptyState from '../../components/common/EmptyState.jsx';
import { getMyBids } from '../../services/bidService.js';

export default function BidderBidsPage() {
  const [bids, setBids] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchBids = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getMyBids();
      setBids(data || []);
    } catch (err) {
      setError(err.message || 'Unable to load bid submissions.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBids();
  }, [fetchBids]);

  const getStatusBadge = (status) => {
    const s = (status || '').toUpperCase();
    if (s === 'SUBMITTED') {
      return <Badge variant="success">Submitted</Badge>;
    }
    return <Badge variant="warning">Draft Workspace</Badge>;
  };

  const draftCount = bids.filter((b) => (b.status || '').toUpperCase() === 'DRAFT').length;
  const submittedCount = bids.filter((b) => (b.status || '').toUpperCase() === 'SUBMITTED').length;

  return (
    <PageContainer
      title="My Tender Bids"
      subtitle="Manage your tender submission workspaces, attached documents, and statutory evaluation proposals"
      actions={
        <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
          <Link to="/bidder" style={{ textDecoration: 'none' }}>
            <Button variant="outline" size="sm">
              ← Workspace
            </Button>
          </Link>
          <Link to="/bidder/tenders" style={{ textDecoration: 'none' }}>
            <Button variant="primary" size="sm">
              Browse Tenders
            </Button>
          </Link>
        </div>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
        {/* Notice Banner */}
        <div
          style={{
            backgroundColor: 'var(--color-bg-card)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-4) var(--space-5)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: 'var(--space-3)',
          }}
        >
          <div>
            <span style={{ fontSize: 'var(--font-size-sm)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-primary)' }}>
              Submission Lifecycle Overview
            </span>
            <p style={{ margin: 'var(--space-1) 0 0 0', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
              Drafts allow document upload and OCR/AI processing. Submitting locks the proposal for official review without automatic qualification or award.
            </p>
          </div>
          <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
            <div style={{ textAlign: 'center', padding: 'var(--space-2) var(--space-4)', backgroundColor: 'var(--color-bg-muted)', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: 'var(--font-size-lg)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)' }}>
                {bids.length}
              </div>
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>Total Bids</div>
            </div>
            <div style={{ textAlign: 'center', padding: 'var(--space-2) var(--space-4)', backgroundColor: 'var(--color-bg-muted)', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: 'var(--font-size-lg)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-warning, #eab308)' }}>
                {draftCount}
              </div>
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>Drafts</div>
            </div>
            <div style={{ textAlign: 'center', padding: 'var(--space-2) var(--space-4)', backgroundColor: 'var(--color-bg-muted)', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: 'var(--font-size-lg)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-success, #22c55e)' }}>
                {submittedCount}
              </div>
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>Submitted</div>
            </div>
          </div>
        </div>

        {/* Content Area */}
        {loading ? (
          <div style={{ padding: 'var(--space-8)', textAlign: 'center' }}>
            <Loading message="Loading your tender bids..." size="lg" />
          </div>
        ) : error ? (
          <div
            style={{
              backgroundColor: 'var(--color-danger-subtle, #fee2e2)',
              border: '1px solid var(--color-danger, #ef4444)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-4)',
              color: 'var(--color-danger, #ef4444)',
              fontSize: 'var(--font-size-sm)',
            }}
          >
            ⚠️ {error}
          </div>
        ) : bids.length === 0 ? (
          <div
            style={{
              backgroundColor: 'var(--color-bg-card)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-8)',
            }}
          >
            <EmptyState
              title="No bids yet"
              description="You have not started any tender submissions yet. Browse active published tenders to open your first proposal workspace."
              action={
                <Link to="/bidder/tenders" style={{ textDecoration: 'none' }}>
                  <Button variant="primary">Browse Available Tenders</Button>
                </Link>
              }
            />
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 'var(--space-4)' }}>
            {bids.map((bid) => {
              const isSubmitted = (bid.status || '').toUpperCase() === 'SUBMITTED';
              return (
                <div
                  key={bid.id}
                  style={{
                    backgroundColor: 'var(--color-bg-card)',
                    border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-md)',
                    padding: 'var(--space-5)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    gap: 'var(--space-4)',
                    boxShadow: 'var(--shadow-xs)',
                    transition: 'border-color var(--transition-fast)',
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--color-primary)'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--color-border)'; }}
                >
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)', maxWidth: '650px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                      {getStatusBadge(bid.status)}
                      <span style={{ fontSize: 'var(--font-size-xs)', fontFamily: 'var(--font-mono)', color: 'var(--color-text-muted)' }}>
                        Ref: {bid.tender_reference_number || 'N/A'}
                      </span>
                    </div>
                    <h3 style={{ margin: 0, fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-primary)' }}>
                      {bid.tender_title || 'Tender Workspace'}
                    </h3>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                      <span>📄 Documents Attached: <strong>{bid.documents_count ?? (bid.documents?.length || 0)}</strong></span>
                      <span>📅 Created: {new Date(bid.created_at).toLocaleDateString()}</span>
                      {isSubmitted && bid.submitted_at && (
                        <span style={{ color: 'var(--color-success, #22c55e)' }}>
                          ✓ Submitted: {new Date(bid.submitted_at).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                    <Link to={`/bidder/bids/${bid.id}/compliance`} style={{ textDecoration: 'none' }}>
                      <Button variant="secondary" size="sm">
                        Compliance Score →
                      </Button>
                    </Link>
                    <Link to={`/bidder/bids/${bid.id}`} style={{ textDecoration: 'none' }}>
                      <Button variant={isSubmitted ? 'outline' : 'primary'} size="sm">
                        {isSubmitted ? 'View Workspace' : 'Continue Proposal →'}
                      </Button>
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </PageContainer>
  );
}
