import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import PageContainer from '../../components/layout/PageContainer.jsx';
import Badge from '../../components/common/Badge.jsx';
import Button from '../../components/common/Button.jsx';
import Loading from '../../components/common/Loading.jsx';
import EmptyState from '../../components/common/EmptyState.jsx';
import Modal from '../../components/common/Modal.jsx';
import { getTenders, getTenderById } from '../../services/tenderService.js';
import { createOrGetTenderBid } from '../../services/bidService.js';


export default function BidderTendersPage() {
  const navigate = useNavigate();
  const [tenders, setTenders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedTender, setSelectedTender] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [startingBid, setStartingBid] = useState(false);


  const fetchTenders = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getTenders();
      setTenders(data.items || []);
    } catch (err) {
      setError(err.message || 'Unable to load tenders.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTenders();
  }, [fetchTenders]);

  const handleOpenDetail = async (tenderSummary) => {
    setSelectedTender(tenderSummary);
    setDetailLoading(true);
    try {
      const fullTender = await getTenderById(tenderSummary.reference_number || tenderSummary.id);
      setSelectedTender(fullTender || tenderSummary);
    } catch {
      // Keep summary data if full detail fails
    } finally {
      setDetailLoading(false);
    }
  };

  const handleStartBid = async () => {
    if (!selectedTender) return;
    setStartingBid(true);
    try {
      const bid = await createOrGetTenderBid(selectedTender.id);
      setSelectedTender(null);
      navigate(`/bidder/bids/${bid.id}`);
    } catch (err) {
      alert(err.message || 'Unable to open bid workspace.');
    } finally {
      setStartingBid(false);
    }
  };


  const filteredTenders = tenders.filter((t) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      (t.title && t.title.toLowerCase().includes(q)) ||
      (t.reference_number && t.reference_number.toLowerCase().includes(q)) ||
      (t.organization && t.organization.toLowerCase().includes(q))
    );
  });

  const getStatusBadge = (status) => {
    const s = (status || '').toUpperCase();
    switch (s) {
      case 'ACTIVE':
        return <Badge variant="success">Active</Badge>;
      case 'UNDER_REVIEW':
      case 'REVIEW':
        return <Badge variant="warning">Under Review</Badge>;
      case 'CLOSED':
        return <Badge variant="neutral">Closed</Badge>;
      default:
        return <Badge variant="info">{status || 'Draft'}</Badge>;
    }
  };

  return (
    <PageContainer
      title="Browse Published Tenders"
      subtitle="Public procurement opportunities open for statutory evaluation and bidding"
      actions={
        <Link to="/bidder" style={{ textDecoration: 'none' }}>
          <Button variant="outline" size="sm">
            ← Back to Workspace
          </Button>
        </Link>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
        {/* Search & Filter Bar */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: 'var(--space-3)',
            flexWrap: 'wrap',
          }}
        >
          <input
            type="text"
            placeholder="Search by tender title, reference, or organisation..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              padding: 'var(--space-2) var(--space-3)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border)',
              backgroundColor: 'var(--color-bg-card)',
              color: 'var(--color-text-primary)',
              fontSize: 'var(--font-size-sm)',
              minWidth: '320px',
              maxWidth: '500px',
              flex: 1,
            }}
          />
          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
            Showing {filteredTenders.length} of {tenders.length} tenders
          </span>
        </div>

        {loading ? (
          <div style={{ padding: 'var(--space-8)', textAlign: 'center' }}>
            <Loading message="Fetching live procurement tenders..." size="lg" />
          </div>
        ) : error ? (
          <EmptyState
            title="Unable to load tenders"
            description={error}
            actionLabel="Retry"
            onAction={fetchTenders}
          />
        ) : filteredTenders.length === 0 ? (
          <EmptyState
            title="No tenders found"
            description={searchQuery ? 'No tenders match your search criteria.' : 'There are currently no published procurement tenders available.'}
          />
        ) : (
          <div
            style={{
              backgroundColor: 'var(--color-bg-card)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-border)',
              boxShadow: 'var(--shadow-xs)',
              overflow: 'hidden',
            }}
          >
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--font-size-sm)' }}>
                <thead>
                  <tr
                    style={{
                      backgroundColor: 'var(--color-bg-subtle)',
                      borderBottom: '1px solid var(--color-border)',
                      fontSize: 'var(--font-size-xs)',
                      color: 'var(--color-text-muted)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em',
                      textAlign: 'left',
                    }}
                  >
                    <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Reference</th>
                    <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Tender Title</th>
                    <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Procuring Organisation</th>
                    <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Status</th>
                    <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Estimated Value</th>
                    <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Closing Date</th>
                    <th style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'right' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTenders.map((tender, index) => {
                    const tenderRef = tender.reference_number || tender.id;
                    return (
                      <tr
                        key={tender.id}
                        style={{
                          borderBottom: index === filteredTenders.length - 1 ? 'none' : '1px solid var(--color-border-subtle)',
                          transition: 'background-color var(--transition-fast)',
                        }}
                        onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'var(--color-bg-hover)'; }}
                        onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; }}
                      >
                        <td style={{ padding: 'var(--space-3) var(--space-4)', fontFamily: 'var(--font-family-mono)', fontSize: 'var(--font-size-xs)', color: 'var(--color-primary)' }}>
                          {tenderRef}
                        </td>
                        <td style={{ padding: 'var(--space-3) var(--space-4)', fontWeight: 'var(--font-weight-medium)', color: 'var(--color-text-primary)' }}>
                          {tender.title}
                        </td>
                        <td style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--color-text-secondary)' }}>
                          {tender.organization || 'Ministry / CPSE'}
                        </td>
                        <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                          {getStatusBadge(tender.status)}
                        </td>
                        <td style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--color-text-primary)', fontFamily: 'var(--font-family-mono)', fontSize: 'var(--font-size-xs)' }}>
                          {tender.value || '₹ —'}
                        </td>
                        <td style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--color-text-muted)', fontSize: 'var(--font-size-xs)' }}>
                          {tender.closingDate || '—'}
                        </td>
                        <td style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'right' }}>
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => handleOpenDetail(tender)}
                          >
                            Inspect
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

        {/* Read-Only Tender Inspection Modal */}
        {selectedTender && (
          <Modal
            isOpen={Boolean(selectedTender)}
            onClose={() => setSelectedTender(null)}
            title={`Tender Inspection: ${selectedTender.reference_number || selectedTender.id}`}
          >
            {detailLoading ? (
              <div style={{ padding: 'var(--space-6)', textAlign: 'center' }}>
                <Loading message="Loading tender details..." />
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: 'var(--font-size-lg)', color: 'var(--color-text-primary)' }}>
                    {selectedTender.title}
                  </h3>
                  <div style={{ display: 'flex', gap: 'var(--space-2)', marginTop: 'var(--space-2)' }}>
                    {getStatusBadge(selectedTender.status)}
                    <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                      Organisation: {selectedTender.organization || 'Public Sector / Ministry'}
                    </span>
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Description &amp; Scope of Work
                  </div>
                  <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', marginTop: 'var(--space-1)', lineHeight: 1.5 }}>
                    {selectedTender.description || 'No detailed scope description provided.'}
                  </p>
                </div>

                <div
                  style={{
                    backgroundColor: 'var(--color-primary-subtle)',
                    border: '1px solid var(--color-primary)',
                    borderRadius: 'var(--radius-sm)',
                    padding: 'var(--space-3) var(--space-4)',
                    fontSize: 'var(--font-size-xs)',
                    color: 'var(--color-text-primary)',
                  }}
                >
                  <strong>Bid Submission Workspace:</strong>
                  <p style={{ margin: 'var(--space-1) 0 0 0', color: 'var(--color-text-secondary)' }}>
                    Prepare your formal statutory proposal, upload compliance certificates, and track automated OCR/AI extraction in a dedicated workspace.
                  </p>
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--space-2)', marginTop: 'var(--space-2)' }}>
                  <Button variant="secondary" onClick={() => setSelectedTender(null)}>
                    Close
                  </Button>
                  <Button
                    variant="primary"
                    disabled={startingBid}
                    onClick={handleStartBid}
                  >
                    {startingBid ? 'Opening Workspace...' : 'Start / Open Bid Workspace →'}
                  </Button>
                </div>

              </div>
            )}
          </Modal>
        )}
      </div>
    </PageContainer>
  );
}
