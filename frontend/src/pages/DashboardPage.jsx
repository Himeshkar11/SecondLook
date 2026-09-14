import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import PageContainer from '../components/layout/PageContainer.jsx';
import StatCard from '../components/cards/StatCard.jsx';
import Badge from '../components/common/Badge.jsx';
import Button from '../components/common/Button.jsx';
import Loading from '../components/common/Loading.jsx';
import EmptyState from '../components/common/EmptyState.jsx';
import { getOfficerDashboardOverview } from '../services/dashboardService.js';

/**
 * Officer Operational Dashboard (Milestone 10)
 * Aggregates authorized tenders, bidder activity, document processing,
 * compliance evaluation progress, and itemized attention notices.
 *
 * Strict Decision Safety:
 * All compliance scores and evaluation results are informational decision support tools.
 * Authoritative decisions (qualification, rejection, award) remain strictly with the officer.
 */
export default function DashboardPage() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getOfficerDashboardOverview();
      setData(response);
    } catch (err) {
      console.error('Failed to load officer dashboard:', err);
      setError(err?.response?.data?.detail || err.message || 'Failed to load officer dashboard overview.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  const getTenderStatusBadge = (status) => {
    const s = String(status || '').toUpperCase();
    switch (s) {
      case 'ACTIVE':
      case 'PUBLISHED':
        return <Badge variant="success">Active</Badge>;
      case 'UNDER_REVIEW':
      case 'REVIEW':
        return <Badge variant="warning">Under Review</Badge>;
      case 'EVALUATING':
      case 'IN_EVALUATION':
        return <Badge variant="info">Evaluating</Badge>;
      case 'CLOSED':
      case 'ARCHIVED':
        return <Badge variant="neutral">Closed</Badge>;
      case 'DRAFT':
        return <Badge variant="neutral">Draft</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };

  const getSeverityBadge = (severity) => {
    const sev = String(severity || '').toUpperCase();
    switch (sev) {
      case 'HIGH':
        return <Badge variant="danger">High</Badge>;
      case 'MEDIUM':
        return <Badge variant="warning">Medium</Badge>;
      case 'LOW':
        return <Badge variant="info">Low</Badge>;
      default:
        return <Badge variant="neutral">{severity}</Badge>;
    }
  };

  if (loading && !data) {
    return (
      <PageContainer
        title="Officer Dashboard"
        subtitle="Procurement oversight, bidder evaluations, and statutory compliance status"
      >
        <Loading message="Loading procurement overview and compliance items..." />
      </PageContainer>
    );
  }

  if (error && !data) {
    return (
      <PageContainer
        title="Officer Dashboard"
        subtitle="Procurement oversight, bidder evaluations, and statutory compliance status"
      >
        <div
          role="alert"
          style={{
            padding: 'var(--space-6)',
            backgroundColor: 'var(--color-bg-card)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--color-danger, #ef4444)',
            textAlign: 'center',
          }}
        >
          <p style={{ color: 'var(--color-danger, #ef4444)', fontWeight: 'var(--font-weight-semibold)', marginBottom: 'var(--space-3)' }}>
            {error}
          </p>
          <Button variant="primary" size="sm" onClick={fetchDashboard}>
            Retry
          </Button>
        </div>
      </PageContainer>
    );
  }

  const overview = data?.overview || {
    active_tenders: 0,
    total_tenders: 0,
    bids_received: 0,
    evaluations_pending: 0,
    reviews_requiring_attention: 0,
  };

  const tenders = data?.tenders || [];
  const attentionItems = data?.attention_items || [];

  // Filter and search tenders
  const filteredTenders = tenders.filter((tender) => {
    const matchesSearch =
      (tender.reference_number && tender.reference_number.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (tender.title && tender.title.toLowerCase().includes(searchQuery.toLowerCase()));

    if (!matchesSearch) return false;

    if (filterStatus === 'ALL') return true;
    if (filterStatus === 'ACTIVE') return tender.status?.toUpperCase() === 'ACTIVE' || tender.status?.toUpperCase() === 'PUBLISHED';
    if (filterStatus === 'UNDER_REVIEW') return tender.status?.toUpperCase() === 'UNDER_REVIEW' || tender.status?.toUpperCase() === 'REVIEW';
    if (filterStatus === 'ATTENTION') return Boolean(tender.has_attention);
    return true;
  });

  return (
    <PageContainer
      title="Officer Compliance Dashboard"
      subtitle="Procurement oversight, bidder submissions, automated compliance checks, and statutory review"
      actions={
        <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
          <Button variant="ghost" size="sm" onClick={fetchDashboard} disabled={loading}>
            {loading ? 'Refreshing...' : 'Refresh'}
          </Button>
          <Button variant="secondary" size="sm" onClick={() => navigate('/officer/audit')}>
            Audit Log
          </Button>
          <Button variant="secondary" size="sm" onClick={() => navigate('/officer/evaluations')}>
            Verification Engine
          </Button>
        </div>
      }
    >
      {/* 0. Informational Notice — Decision Safety */}
      <div
        style={{
          padding: 'var(--space-3) var(--space-4)',
          marginBottom: 'var(--space-5)',
          borderRadius: 'var(--radius-md)',
          backgroundColor: 'var(--color-bg-subtle, #f8fafc)',
          borderLeft: '4px solid var(--color-primary, #1e40af)',
          border: '1px solid var(--color-border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: 'var(--font-size-xs)',
          color: 'var(--color-text-secondary)',
        }}
      >
        <div>
          <strong style={{ color: 'var(--color-text-primary)' }}>Advisory Notice:</strong> Automated compliance scores and AI evidence extractions are informational decision support tools. All qualification, rejection, and tender award decisions must be explicitly determined and recorded by the designated procurement officer.
        </div>
      </div>

      {/* 1. Stat Cards Row */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: 'var(--space-4)',
          marginBottom: 'var(--space-6)',
        }}
      >
        <StatCard
          title="Active Tenders"
          value={overview.active_tenders}
          context={`${overview.total_tenders} total authorized`}
          badgeText="Active"
          badgeVariant="success"
        />
        <StatCard
          title="Bids Received"
          value={overview.bids_received}
          context="Across active tenders"
          badgeText="Bids"
          badgeVariant="info"
        />
        <StatCard
          title="Evaluations Pending"
          value={overview.evaluations_pending}
          context="Require automated or statutory checks"
          badgeText={overview.evaluations_pending > 0 ? 'Pending' : 'Done'}
          badgeVariant={overview.evaluations_pending > 0 ? 'warning' : 'neutral'}
        />
        <StatCard
          title="Reviews Requiring Attention"
          value={overview.reviews_requiring_attention}
          context="Unreviewed submissions or failed requirements"
          badgeText={overview.reviews_requiring_attention > 0 ? 'Action Req.' : 'Clear'}
          badgeVariant={overview.reviews_requiring_attention > 0 ? 'danger' : 'success'}
        />
      </div>

      {/* 2. Attention Required Section */}
      <div
        style={{
          marginBottom: 'var(--space-6)',
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
            <h3
              style={{
                fontSize: 'var(--font-size-base)',
                fontWeight: 'var(--font-weight-semibold)',
                color: 'var(--color-text-primary)',
              }}
            >
              Actionable Attention Notices
            </h3>
            <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', margin: 0 }}>
              Flagged items requiring officer review, failed critical requirements, or pending evaluations
            </p>
          </div>
          <Badge variant={attentionItems.length > 0 ? 'warning' : 'success'}>
            {attentionItems.length} {attentionItems.length === 1 ? 'Notice' : 'Notices'}
          </Badge>
        </div>

        {attentionItems.length === 0 ? (
          <div style={{ padding: 'var(--space-6)', textAlign: 'center', color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>
            No immediate attention items. All active tender evaluations and officer reviews are up to date.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {attentionItems.map((item, idx) => (
              <div
                key={`${item.tender_id}-${item.bidder_id || idx}-${item.item_type}`}
                style={{
                  padding: 'var(--space-3) var(--space-5)',
                  borderBottom: idx === attentionItems.length - 1 ? 'none' : '1px solid var(--color-border-subtle)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 'var(--space-4)',
                  backgroundColor: idx % 2 === 0 ? 'transparent' : 'var(--color-bg-subtle, #fcfcfc)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', flex: 1, minWidth: 0 }}>
                  {getSeverityBadge(item.severity)}
                  <div>
                    <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 'var(--font-weight-medium)', color: 'var(--color-text-primary)' }}>
                      {item.message}
                    </div>
                    <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                      Tender Ref: <strong style={{ color: 'var(--color-text-secondary)' }}>{item.tender_reference}</strong>
                      {item.bidder_name && ` · Bidder: ${item.bidder_name}`}
                      {` · Type: ${item.item_type}`}
                    </div>
                  </div>
                </div>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => navigate(item.action_url)}
                  style={{ whiteSpace: 'nowrap' }}
                >
                  Inspect & Review →
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 3. Authorized Procurement Tenders Table */}
      <div
        style={{
          backgroundColor: 'var(--color-bg-card)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--color-border)',
          boxShadow: 'var(--shadow-xs)',
          overflow: 'hidden',
        }}
      >
        {/* Table Toolbar: Title, Filter Tabs & Search */}
        <div
          style={{
            padding: 'var(--space-4) var(--space-5)',
            borderBottom: '1px solid var(--color-border)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-3)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
            <div>
              <h3
                style={{
                  fontSize: 'var(--font-size-base)',
                  fontWeight: 'var(--font-weight-semibold)',
                  color: 'var(--color-text-primary)',
                }}
              >
                Authorized Procurement Tenders
              </h3>
              <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', margin: 0 }}>
                Procurement tenders within your authorized jurisdiction with live evaluation and review tracking
              </p>
            </div>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
              Showing {filteredTenders.length} of {tenders.length} tenders
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-3)' }}>
            {/* Filter Tabs */}
            <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
              {[
                { id: 'ALL', label: 'All Tenders' },
                { id: 'ACTIVE', label: 'Active' },
                { id: 'UNDER_REVIEW', label: 'Under Review' },
                { id: 'ATTENTION', label: 'Attention Required' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setFilterStatus(tab.id)}
                  style={{
                    padding: '4px 12px',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: 'var(--font-size-xs)',
                    fontWeight: filterStatus === tab.id ? 'var(--font-weight-semibold)' : 'var(--font-weight-normal)',
                    border: '1px solid',
                    borderColor: filterStatus === tab.id ? 'var(--color-primary)' : 'var(--color-border)',
                    backgroundColor: filterStatus === tab.id ? 'var(--color-primary-subtle, #eff6ff)' : 'transparent',
                    color: filterStatus === tab.id ? 'var(--color-primary)' : 'var(--color-text-secondary)',
                    cursor: 'pointer',
                  }}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Search Input */}
            <div style={{ minWidth: 240, maxWidth: 360, flex: 1 }}>
              <input
                type="text"
                placeholder="Search reference or title..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  width: '100%',
                  padding: '6px 12px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--color-border)',
                  fontSize: 'var(--font-size-xs)',
                  backgroundColor: 'var(--color-bg-card)',
                  color: 'var(--color-text-primary)',
                }}
              />
            </div>
          </div>
        </div>

        {/* Table Content */}
        <div style={{ overflowX: 'auto' }}>
          {filteredTenders.length === 0 ? (
            <div style={{ padding: 'var(--space-8)' }}>
              <EmptyState
                title="No Tenders Found"
                description={
                  searchQuery || filterStatus !== 'ALL'
                    ? 'No procurement tenders match your selected filters or search criteria.'
                    : 'No authorized tenders are currently registered in your officer jurisdiction.'
                }
              />
            </div>
          ) : (
            <table style={{ width: '100%', fontSize: 'var(--font-size-sm)', borderCollapse: 'collapse' }}>
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
                  <th style={{ padding: 'var(--space-3) var(--space-5)', textAlign: 'left' }}>Tender Reference & Title</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'center' }}>Status</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'center' }}>Bidders / Bids</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'center' }}>Requirements</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'center' }}>Evaluation Progress</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'center' }}>Attention</th>
                  <th style={{ padding: 'var(--space-3) var(--space-5)', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredTenders.map((tender, index) => (
                  <tr
                    key={tender.id}
                    style={{
                      borderBottom: index === filteredTenders.length - 1 ? 'none' : '1px solid var(--color-border-subtle)',
                      transition: 'background-color var(--transition-fast)',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = 'var(--color-bg-hover)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }}
                  >
                    {/* Tender Ref & Title */}
                    <td style={{ padding: 'var(--space-3) var(--space-5)' }}>
                      <div
                        style={{
                          fontWeight: 'var(--font-weight-medium)',
                          color: 'var(--color-primary)',
                          cursor: 'pointer',
                        }}
                        onClick={() => navigate(`/officer/tenders/${encodeURIComponent(tender.id)}`)}
                      >
                        {tender.reference_number || tender.id}
                      </div>
                      <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                        {tender.title}
                      </div>
                    </td>

                    {/* Status */}
                    <td style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'center' }}>
                      {getTenderStatusBadge(tender.status)}
                    </td>

                    {/* Bidders / Bids */}
                    <td style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'center', fontSize: 'var(--font-size-xs)' }}>
                      <div><strong style={{ color: 'var(--color-text-primary)' }}>{tender.bids_count}</strong> bids</div>
                      <div style={{ color: 'var(--color-text-muted)' }}>{tender.bidders_count} bidders</div>
                    </td>

                    {/* Requirements */}
                    <td style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'center', fontSize: 'var(--font-size-xs)' }}>
                      <span style={{ fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-primary)' }}>
                        {tender.requirements_count}
                      </span>
                    </td>

                    {/* Evaluation Progress */}
                    <td style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'center', fontSize: 'var(--font-size-xs)' }}>
                      <div>
                        <strong style={{ color: 'var(--color-text-primary)' }}>{tender.evaluations_count}</strong> evaluations
                      </div>
                      <div style={{ color: tender.reviews_pending_count > 0 ? 'var(--color-warning, #b45309)' : 'var(--color-text-muted)' }}>
                        {tender.reviews_pending_count > 0 ? `${tender.reviews_pending_count} reviews pending` : 'Reviews up to date'}
                      </div>
                    </td>

                    {/* Attention */}
                    <td style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'center' }}>
                      {tender.has_attention ? (
                        <Badge variant="warning">Action Req</Badge>
                      ) : (
                        <Badge variant="neutral">Normal</Badge>
                      )}
                    </td>

                    {/* Actions */}
                    <td style={{ padding: 'var(--space-3) var(--space-5)', textAlign: 'right' }}>
                      <div style={{ display: 'flex', gap: 'var(--space-2)', justifyContent: 'flex-end' }}>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => navigate(`/officer/tenders/${encodeURIComponent(tender.id)}`)}
                        >
                          Requirements
                        </Button>
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => navigate(`/officer/tenders/${encodeURIComponent(tender.id)}/dashboard`)}
                        >
                          Workflow →
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </PageContainer>
  );
}
