import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import PageContainer from '../../components/layout/PageContainer.jsx';
import Badge from '../../components/common/Badge.jsx';
import Button from '../../components/common/Button.jsx';
import Loading from '../../components/common/Loading.jsx';
import {
  getBidCompliance,
  getBidComplianceHistory,
  getDocumentAccess,
} from '../../services/bidService.js';

export default function BidderBidCompliancePage() {
  const { bidId } = useParams();
  const [compliance, setCompliance] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [accessError, setAccessError] = useState(null);
  const [activeFilter, setActiveFilter] = useState('ALL'); // 'ALL' | 'ATTENTION' | 'PASSED'

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [compData, histData] = await Promise.all([
        getBidCompliance(bidId),
        getBidComplianceHistory(bidId).catch(() => []),
      ]);
      setCompliance(compData);
      setHistory(histData || []);
    } catch (err) {
      setError(err.message || 'Unable to load compliance assessment.');
    } finally {
      setLoading(false);
    }
  }, [bidId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleDocumentAccess = async (docId) => {
    if (!docId) return;
    setAccessError(null);
    try {
      const res = await getDocumentAccess(docId);
      if (res?.download_url || res?.url) {
        window.open(res.download_url || res.url, '_blank', 'noopener,noreferrer');
      } else {
        setAccessError('Unable to generate temporary secure access URL.');
      }
    } catch (err) {
      setAccessError(err.message || 'Failed to access document.');
    }
  };

  if (loading) {
    return (
      <PageContainer title="Bid Compliance Assessment" subtitle="Loading statutory evaluation details...">
        <div style={{ padding: 'var(--space-8)', textAlign: 'center' }}>
          <Loading message="Loading compliance results..." size="lg" />
        </div>
      </PageContainer>
    );
  }

  if (error || !compliance) {
    return (
      <PageContainer title="Bid Compliance Assessment" subtitle="Error loading compliance">
        <div
          style={{
            backgroundColor: 'var(--color-danger-subtle, #fee2e2)',
            border: '1px solid var(--color-danger, #ef4444)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-5)',
            color: 'var(--color-danger, #ef4444)',
            fontSize: 'var(--font-size-sm)',
          }}
        >
          ⚠️ {error || 'Compliance data not available.'}
        </div>
        <div style={{ marginTop: 'var(--space-4)' }}>
          <Link to={`/bidder/bids/${bidId}`} style={{ textDecoration: 'none' }}>
            <Button variant="outline">← Back to Bid Workspace</Button>
          </Link>
        </div>
      </PageContainer>
    );
  }

  const { summary, requirements = [] } = compliance;
  const isNotEvaluated = compliance.status === 'NOT_EVALUATED';
  const isProcessing = ['PENDING', 'PROCESSING'].includes(compliance.status);

  // Status badge styling helper
  const getStatusBadge = (status) => {
    const s = (status || '').toUpperCase();
    if (s === 'PASS') return <Badge variant="success">PASS</Badge>;
    if (s === 'FAIL') return <Badge variant="danger">FAIL</Badge>;
    if (s === 'PARTIAL') return <Badge variant="warning">PARTIAL</Badge>;
    if (s === 'NOT_VERIFIED') return <Badge variant="neutral">NOT VERIFIED</Badge>;
    if (s === 'NOT_APPLICABLE') return <Badge variant="neutral">NOT APPLICABLE</Badge>;
    return <Badge variant="neutral">{s || 'PENDING'}</Badge>;
  };

  // Filter requirements
  const attentionRequirements = requirements.filter((r) =>
    ['FAIL', 'PARTIAL', 'NOT_VERIFIED'].includes((r.status || '').toUpperCase())
  );
  const passedRequirements = requirements.filter(
    (r) => (r.status || '').toUpperCase() === 'PASS'
  );

  let displayedRequirements = requirements;
  if (activeFilter === 'ATTENTION') {
    displayedRequirements = attentionRequirements;
  } else if (activeFilter === 'PASSED') {
    displayedRequirements = passedRequirements;
  }

  return (
    <PageContainer
      title={`Compliance Assessment: ${compliance.tender_title || 'Tender Proposal'}`}
      subtitle={`Reference: ${compliance.tender_reference_number || 'N/A'} | Evaluation State: ${compliance.status}`}
      actions={
        <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
          <Link to={`/bidder/bids/${bidId}`} style={{ textDecoration: 'none' }}>
            <Button variant="outline" size="sm">
              ← Bid Workspace
            </Button>
          </Link>
          <Link to="/bidder/bids" style={{ textDecoration: 'none' }}>
            <Button variant="outline" size="sm">
              All Bids
            </Button>
          </Link>
        </div>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
        {/* Authoritative Non-Qualification Disclaimer Notice */}
        <div
          style={{
            backgroundColor: 'var(--color-primary-subtle, #eff6ff)',
            border: '1px solid var(--color-primary, #3b82f6)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-4) var(--space-5)',
            color: 'var(--color-text-primary)',
            fontSize: 'var(--font-size-xs)',
            lineHeight: 1.5,
          }}
        >
          <div style={{ fontWeight: 'var(--font-weight-semibold)', marginBottom: 'var(--space-1)' }}>
            ℹ️ Informational Assessment Notice
          </div>
          <div>{compliance.disclaimer}</div>
        </div>

        {accessError && (
          <div
            style={{
              backgroundColor: 'var(--color-danger-subtle, #fee2e2)',
              border: '1px solid var(--color-danger, #ef4444)',
              borderRadius: 'var(--radius-sm)',
              padding: 'var(--space-3) var(--space-4)',
              color: 'var(--color-danger, #ef4444)',
              fontSize: 'var(--font-size-xs)',
            }}
          >
            ⚠️ {accessError}
          </div>
        )}

        {/* Empty / Honest State: Not Evaluated */}
        {isNotEvaluated ? (
          <div
            style={{
              backgroundColor: 'var(--color-bg-card)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-8)',
              textAlign: 'center',
              boxShadow: 'var(--shadow-xs)',
            }}
          >
            <div style={{ fontSize: '3rem', marginBottom: 'var(--space-3)' }}>⏳</div>
            <h3 style={{ margin: '0 0 var(--space-2) 0', fontSize: 'var(--font-size-lg)', fontWeight: 'var(--font-weight-semibold)' }}>
              Compliance Evaluation Not Started
            </h3>
            <p style={{ margin: '0 auto var(--space-5) auto', maxWidth: '600px', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
              {compliance.message || 'Once procurement officers initiate statutory evaluation of submitted proposals, your compliance results and score will appear here.'}
            </p>
            <Link to={`/bidder/bids/${bidId}`} style={{ textDecoration: 'none' }}>
              <Button variant="primary">Return to Bid Workspace</Button>
            </Link>
          </div>
        ) : isProcessing ? (
          /* Processing State */
          <div
            style={{
              backgroundColor: 'var(--color-bg-card)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-8)',
              textAlign: 'center',
              boxShadow: 'var(--shadow-xs)',
            }}
          >
            <div style={{ fontSize: '3rem', marginBottom: 'var(--space-3)' }}>⚙️</div>
            <h3 style={{ margin: '0 0 var(--space-2) 0', fontSize: 'var(--font-size-lg)', fontWeight: 'var(--font-weight-semibold)' }}>
              Compliance Evaluation in Progress
            </h3>
            <p style={{ margin: '0 auto', maxWidth: '600px', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
              Statutory verification and rule checks are currently being processed. Please refresh in a moment to view completed outcomes.
            </p>
          </div>
        ) : (
          /* Completed Compliance Overview */
          <>
            {/* Top Score & Summary Banner */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: 'var(--space-4)',
              }}
            >
              {/* Score Card */}
              <div
                style={{
                  backgroundColor: 'var(--color-bg-card)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--space-5)',
                  boxShadow: 'var(--shadow-xs)',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                }}
              >
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', fontWeight: 'var(--font-weight-medium)' }}>
                  Compliance Score
                </div>
                <div
                  style={{
                    fontSize: '2.5rem',
                    fontWeight: 'var(--font-weight-bold)',
                    color: compliance.score !== null ? (compliance.score >= 80 ? 'var(--color-success, #22c55e)' : 'var(--color-warning, #eab308)') : 'var(--color-text-muted)',
                    margin: 'var(--space-1) 0',
                    lineHeight: 1,
                  }}
                >
                  {compliance.score_formatted}
                </div>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                  {summary?.applicable_count ?? 0} applicable requirements evaluated
                </div>
              </div>

              {/* Passed Card */}
              <div
                style={{
                  backgroundColor: 'var(--color-bg-card)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--space-5)',
                  boxShadow: 'var(--shadow-xs)',
                }}
              >
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', fontWeight: 'var(--font-weight-medium)' }}>
                  Passed Requirements
                </div>
                <div style={{ fontSize: '2rem', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-success, #22c55e)', margin: 'var(--space-1) 0' }}>
                  {summary?.pass_count ?? 0}
                </div>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                  {summary?.mandatory_passed ?? 0} mandatory / {summary?.optional_passed ?? 0} optional
                </div>
              </div>

              {/* Needs Attention Card */}
              <div
                style={{
                  backgroundColor: 'var(--color-bg-card)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--space-5)',
                  boxShadow: 'var(--shadow-xs)',
                }}
              >
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', fontWeight: 'var(--font-weight-medium)' }}>
                  Needs Attention
                </div>
                <div
                  style={{
                    fontSize: '2rem',
                    fontWeight: 'var(--font-weight-bold)',
                    color: attentionRequirements.length > 0 ? 'var(--color-danger, #ef4444)' : 'var(--color-text-muted)',
                    margin: 'var(--space-1) 0',
                  }}
                >
                  {attentionRequirements.length}
                </div>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                  {summary?.fail_count ?? 0} failed • {summary?.partial_count ?? 0} partial • {summary?.not_verified_count ?? 0} unverified
                </div>
              </div>

              {/* Mandatory Compliance Card */}
              <div
                style={{
                  backgroundColor: 'var(--color-bg-card)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--space-5)',
                  boxShadow: 'var(--shadow-xs)',
                }}
              >
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', fontWeight: 'var(--font-weight-medium)' }}>
                  Mandatory Status
                </div>
                <div style={{ fontSize: '2rem', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)', margin: 'var(--space-1) 0' }}>
                  {summary?.mandatory_passed ?? 0} / {summary?.mandatory_total ?? 0}
                </div>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                  {summary?.mandatory_failed ?? 0} failed • {summary?.mandatory_not_verified ?? 0} unverified
                </div>
              </div>
            </div>

            {/* Filter Navigation Tabs */}
            <div
              style={{
                display: 'flex',
                gap: 'var(--space-2)',
                borderBottom: '1px solid var(--color-border)',
                paddingBottom: 'var(--space-2)',
              }}
            >
              <button
                type="button"
                onClick={() => setActiveFilter('ALL')}
                style={{
                  background: 'none',
                  border: 'none',
                  padding: 'var(--space-2) var(--space-4)',
                  fontSize: 'var(--font-size-sm)',
                  fontWeight: activeFilter === 'ALL' ? 'var(--font-weight-semibold)' : 'normal',
                  color: activeFilter === 'ALL' ? 'var(--color-primary)' : 'var(--color-text-secondary)',
                  borderBottom: activeFilter === 'ALL' ? '2px solid var(--color-primary)' : '2px solid transparent',
                  cursor: 'pointer',
                }}
              >
                All Requirements ({requirements.length})
              </button>
              <button
                type="button"
                onClick={() => setActiveFilter('ATTENTION')}
                style={{
                  background: 'none',
                  border: 'none',
                  padding: 'var(--space-2) var(--space-4)',
                  fontSize: 'var(--font-size-sm)',
                  fontWeight: activeFilter === 'ATTENTION' ? 'var(--font-weight-semibold)' : 'normal',
                  color: activeFilter === 'ATTENTION' ? 'var(--color-danger)' : 'var(--color-text-secondary)',
                  borderBottom: activeFilter === 'ATTENTION' ? '2px solid var(--color-danger)' : '2px solid transparent',
                  cursor: 'pointer',
                }}
              >
                ⚠️ Needs Attention ({attentionRequirements.length})
              </button>
              <button
                type="button"
                onClick={() => setActiveFilter('PASSED')}
                style={{
                  background: 'none',
                  border: 'none',
                  padding: 'var(--space-2) var(--space-4)',
                  fontSize: 'var(--font-size-sm)',
                  fontWeight: activeFilter === 'PASSED' ? 'var(--font-weight-semibold)' : 'normal',
                  color: activeFilter === 'PASSED' ? 'var(--color-success)' : 'var(--color-text-secondary)',
                  borderBottom: activeFilter === 'PASSED' ? '2px solid var(--color-success)' : '2px solid transparent',
                  cursor: 'pointer',
                }}
              >
                ✓ Passed ({passedRequirements.length})
              </button>
            </div>

            {/* Requirement Outcome Cards */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              {displayedRequirements.length === 0 ? (
                <div
                  style={{
                    backgroundColor: 'var(--color-bg-card)',
                    border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-md)',
                    padding: 'var(--space-6)',
                    textAlign: 'center',
                    color: 'var(--color-text-muted)',
                    fontSize: 'var(--font-size-sm)',
                  }}
                >
                  No requirements match the selected filter.
                </div>
              ) : (
                displayedRequirements.map((req) => {
                  const isFail = req.status === 'FAIL';
                  const isPartial = req.status === 'PARTIAL';
                  const isNotVerified = req.status === 'NOT_VERIFIED';

                  return (
                    <div
                      key={req.requirement_id}
                      style={{
                        backgroundColor: 'var(--color-bg-card)',
                        border: '1px solid var(--color-border)',
                        borderLeft: isFail
                          ? '4px solid var(--color-danger, #ef4444)'
                          : isPartial
                          ? '4px solid var(--color-warning, #eab308)'
                          : isNotVerified
                          ? '4px solid var(--color-text-muted, #94a3b8)'
                          : '4px solid var(--color-success, #22c55e)',
                        borderRadius: 'var(--radius-md)',
                        padding: 'var(--space-5)',
                        boxShadow: 'var(--shadow-xs)',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 'var(--space-3)',
                      }}
                    >
                      {/* Card Header */}
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-1)' }}>
                            <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-muted)' }}>
                              {req.requirement_code}
                            </span>
                            {req.mandatory ? (
                              <Badge variant="danger">Mandatory</Badge>
                            ) : (
                              <Badge variant="neutral">Optional</Badge>
                            )}
                            {req.requirement_type && <Badge variant="info">{req.requirement_type}</Badge>}
                          </div>
                          <h4 style={{ margin: 0, fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)' }}>
                            {req.requirement_title}
                          </h4>
                        </div>
                        <div>{getStatusBadge(req.status)}</div>
                      </div>

                      {/* Explanation Section */}
                      {req.explanation && (
                        <div
                          style={{
                            backgroundColor: 'var(--color-bg-subtle)',
                            borderRadius: 'var(--radius-sm)',
                            padding: 'var(--space-3) var(--space-4)',
                            fontSize: 'var(--font-size-sm)',
                            color: 'var(--color-text-primary)',
                            lineHeight: 1.5,
                          }}
                        >
                          <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-1)' }}>
                            Evaluation Rationale:
                          </div>
                          <div>{req.explanation}</div>
                        </div>
                      )}

                      {/* Actionable Guidance (if not passed) */}
                      {req.actionable_guidance && (
                        <div
                          style={{
                            fontSize: 'var(--font-size-xs)',
                            color: isFail ? 'var(--color-danger, #ef4444)' : isPartial ? 'var(--color-warning, #b45309)' : 'var(--color-text-secondary)',
                            display: 'flex',
                            alignItems: 'center',
                            gap: 'var(--space-2)',
                          }}
                        >
                          <span>💡</span>
                          <span>
                            <strong>Actionable Guidance:</strong> {req.actionable_guidance}
                          </span>
                        </div>
                      )}

                      {/* Evidence Trace & Document Access */}
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          flexWrap: 'wrap',
                          gap: 'var(--space-2)',
                          borderTop: '1px solid var(--color-border)',
                          paddingTop: 'var(--space-3)',
                          fontSize: 'var(--font-size-xs)',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                          <span style={{ color: 'var(--color-text-muted)' }}>Evidence Sources:</span>
                          {req.evidence_sources && req.evidence_sources.length > 0 ? (
                            req.evidence_sources.map((src) => (
                              <Badge key={src} variant="neutral">
                                {src}
                              </Badge>
                            ))
                          ) : (
                            <span style={{ color: 'var(--color-text-muted)' }}>None recorded</span>
                          )}
                        </div>

                        {req.document_id && (
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => handleDocumentAccess(req.document_id)}
                          >
                            View Evidence Document
                          </Button>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* Historical Evaluation Runs Section */}
            {history.length > 0 && (
              <div
                style={{
                  backgroundColor: 'var(--color-bg-card)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--space-5)',
                  boxShadow: 'var(--shadow-xs)',
                  marginTop: 'var(--space-4)',
                }}
              >
                <h4 style={{ margin: '0 0 var(--space-3) 0', fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)' }}>
                  Evaluation Run History (Immutable Audit Log)
                </h4>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--font-size-sm)' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--color-border)', textAlign: 'left' }}>
                        <th style={{ padding: 'var(--space-2) var(--space-3)', color: 'var(--color-text-muted)', fontWeight: 'var(--font-weight-medium)' }}>Run ID</th>
                        <th style={{ padding: 'var(--space-2) var(--space-3)', color: 'var(--color-text-muted)', fontWeight: 'var(--font-weight-medium)' }}>Timestamp</th>
                        <th style={{ padding: 'var(--space-2) var(--space-3)', color: 'var(--color-text-muted)', fontWeight: 'var(--font-weight-medium)' }}>Status</th>
                        <th style={{ padding: 'var(--space-2) var(--space-3)', color: 'var(--color-text-muted)', fontWeight: 'var(--font-weight-medium)' }}>Score</th>
                        <th style={{ padding: 'var(--space-2) var(--space-3)', color: 'var(--color-text-muted)', fontWeight: 'var(--font-weight-medium)' }}>Passed / Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {history.map((item) => (
                        <tr key={item.evaluation_id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                          <td style={{ padding: 'var(--space-3)', fontFamily: 'monospace', fontSize: 'var(--font-size-xs)' }}>
                            {String(item.evaluation_id).substring(0, 8)}...
                          </td>
                          <td style={{ padding: 'var(--space-3)', color: 'var(--color-text-secondary)' }}>
                            {new Date(item.created_at).toLocaleString()}
                          </td>
                          <td style={{ padding: 'var(--space-3)' }}>
                            <Badge variant={item.status === 'COMPLETED' ? 'success' : 'neutral'}>{item.status}</Badge>
                          </td>
                          <td style={{ padding: 'var(--space-3)', fontWeight: 'var(--font-weight-bold)' }}>
                            {item.score_formatted}
                          </td>
                          <td style={{ padding: 'var(--space-3)', color: 'var(--color-text-secondary)' }}>
                            {item.pass_count} / {item.total_requirements}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </PageContainer>
  );
}
