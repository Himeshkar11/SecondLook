import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import PageContainer from '../components/layout/PageContainer.jsx';
import Badge from '../components/common/Badge.jsx';
import Button from '../components/common/Button.jsx';
import Loading from '../components/common/Loading.jsx';
import EmptyState from '../components/common/EmptyState.jsx';
import { getBidderById } from '../services/bidderService.js';
import {
  getBidderCompliance,
  evaluateBidderCompliance,
  runComplianceEvaluation,
  getComplianceEvaluation,
  getComplianceEvaluationsHistory,
} from '../services/complianceService.js';
import EvidenceTraceModal from '../components/compliance/EvidenceTraceModal.jsx';
import ComplianceSummary from '../components/compliance/ComplianceSummary.jsx';
import RequirementReview from '../components/compliance/RequirementReview.jsx';
import OfficerReviewPanel from '../components/compliance/OfficerReviewPanel.jsx';
import {
  getReviewPayload,
  createReview,
  updateRequirementReview,
  updateOfficerDecision,
  completeReview,
} from '../services/reviewService.js';

/**
 * BidderDetailPage — Dynamic Supabase-backed bidder profile.
 * Loads statutory details, associated tenders, and documents from FastAPI.
 */
export default function BidderDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const paramTenderId = searchParams.get('tender_id');
  const bidderId = decodeURIComponent(id || '');

  const [bidder, setBidder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notFound, setNotFound] = useState(false);
  const [compliance, setCompliance] = useState(null);
  const [complianceLoading, setComplianceLoading] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [evalError, setEvalError] = useState(null);
  const [evaluationsHistory, setEvaluationsHistory] = useState([]);
  const [selectedEvalId, setSelectedEvalId] = useState(null);
  const [expandedReqs, setExpandedReqs] = useState({});
  const [inspectingReq, setInspectingReq] = useState(null);

  // Task 16 — Officer Review state
  const [reviewPayload, setReviewPayload] = useState(null);
  const [reviewLoading, setReviewLoading] = useState(false);
  const [showReview, setShowReview] = useState(false);

  const toggleReqExpand = (reqKey) => {
    setExpandedReqs((prev) => ({
      ...prev,
      [reqKey]: !prev[reqKey],
    }));
  };

  const fetchBidderDetails = useCallback(async () => {
    if (!bidderId) {
      setNotFound(true);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    setNotFound(false);
    setBidder(null);
    setCompliance(null);
    setEvalError(null);
    setEvaluationsHistory([]);

    try {
      const data = await getBidderById(bidderId);
      setBidder(data);

      const tid = paramTenderId || data?.tender_id || (data?.tenders && data.tenders[0]?.id) || data?.tenderId;
      if (tid) {
        setComplianceLoading(true);
        try {
          // Fetch evaluation history
          const history = await getComplianceEvaluationsHistory(tid, bidderId).catch(() => []);
          const historyList = Array.isArray(history) ? history : [];
          setEvaluationsHistory(historyList);

          if (historyList.length > 0) {
            setSelectedEvalId(historyList[0].evaluation_id);
            const fullEval = await getComplianceEvaluation(historyList[0].evaluation_id);
            setCompliance(fullEval);
          } else {
            // Fallback to latest or initial compliance
            const compData = await getBidderCompliance(bidderId, tid);
            setCompliance(compData);
            if (compData?.evaluation_id) {
              setSelectedEvalId(compData.evaluation_id);
            }
          }
        } catch (cErr) {
          console.error('Failed to load compliance data:', cErr);
          setCompliance(null);
        } finally {
          setComplianceLoading(false);
        }
      }
    } catch (err) {
      if (err?.status === 404 || err?.message?.includes('404')) {
        setNotFound(true);
      } else {
        setError('Unable to load bidder details. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  }, [bidderId, paramTenderId]);

  const handleSelectEvaluation = async (evalId) => {
    if (!evalId || evalId === selectedEvalId) return;
    setSelectedEvalId(evalId);
    setComplianceLoading(true);
    setEvalError(null);
    try {
      const fullEval = await getComplianceEvaluation(evalId);
      setCompliance(fullEval);
    } catch (err) {
      console.error('Failed to load evaluation run:', err);
      setEvalError('Failed to load historical evaluation details.');
    } finally {
      setComplianceLoading(false);
    }
  };

  const handleRunEvaluation = async () => {
    const tid = paramTenderId || bidder?.tender_id || (bidder?.tenders && bidder.tenders[0]?.id) || bidder?.tenderId;
    if (!tid) return;
    setEvaluating(true);
    setEvalError(null);
    try {
      const compData = await runComplianceEvaluation(tid, bidderId);
      setCompliance(compData);
      setSelectedEvalId(compData.evaluation_id);

      // Refresh audit history
      const history = await getComplianceEvaluationsHistory(tid, bidderId).catch(() => []);
      const historyList = Array.isArray(history) ? history : [];
      setEvaluationsHistory(historyList);
    } catch (err) {
      console.error('Compliance evaluation error:', err);
      if (err?.status === 400 && (err?.message?.includes('NO_APPROVED_REQUIREMENTS') || err?.message?.includes('No approved'))) {
        setEvalError('No approved tender requirements are available for evaluation.');
      } else {
        setEvalError(err?.message || 'Compliance evaluation failed.');
      }
    } finally {
      setEvaluating(false);
    }
  };

  // Task 16 — load or refresh review payload
  const loadReviewPayload = useCallback(async (evalId) => {
    if (!evalId) return;
    setReviewLoading(true);
    try {
      const payload = await getReviewPayload(evalId);
      setReviewPayload(payload);
    } catch (err) {
      console.error('Failed to load review payload:', err);
      setReviewPayload(null);
    } finally {
      setReviewLoading(false);
    }
  }, []);

  const handleStartReview = async () => {
    if (!selectedEvalId) return;
    setReviewLoading(true);
    try {
      const payload = await createReview(selectedEvalId, {});
      setReviewPayload(payload);
      setShowReview(true);
    } catch (err) {
      console.error('Failed to start review:', err);
    } finally {
      setReviewLoading(false);
    }
  };

  const handleMarkReviewed = async (requirementResultId, comment) => {
    if (!selectedEvalId) return;
    await updateRequirementReview(selectedEvalId, requirementResultId, {
      status: 'REVIEWED',
      comment,
    });
    await loadReviewPayload(selectedEvalId);
  };

  const handleMarkFlagged = async (requirementResultId, comment) => {
    if (!selectedEvalId) return;
    await updateRequirementReview(selectedEvalId, requirementResultId, {
      status: 'FLAGGED',
      comment,
    });
    await loadReviewPayload(selectedEvalId);
  };

  const handleSaveDecision = async (body) => {
    if (!selectedEvalId) return;
    await updateOfficerDecision(selectedEvalId, body);
    await loadReviewPayload(selectedEvalId);
  };

  const handleCompleteReview = async () => {
    if (!selectedEvalId) return;
    await completeReview(selectedEvalId);
    await loadReviewPayload(selectedEvalId);
  };

  useEffect(() => {
    fetchBidderDetails();
  }, [fetchBidderDetails]);

  // Auto-load review payload when evaluation changes
  useEffect(() => {
    if (selectedEvalId) {
      loadReviewPayload(selectedEvalId);
    }
  }, [selectedEvalId, loadReviewPayload]);

  if (loading) {
    return (
      <PageContainer title="Bidder Profile">
        <Loading message="Loading bidder details..." />
      </PageContainer>
    );
  }

  if (notFound) {
    return (
      <PageContainer title="Bidder Not Found">
        <EmptyState
          title="Bidder not found."
          description="The requested bidder could not be found in the database."
          actionLabel="Back to Bidders"
          onAction={() => navigate('/bidders')}
        />
      </PageContainer>
    );
  }

  if (error || !bidder) {
    return (
      <PageContainer title="Error Loading Bidder">
        <EmptyState
          title="Unable to load bidder details"
          description={error || 'An unexpected error occurred while fetching bidder information.'}
          actionLabel="Retry"
          onAction={fetchBidderDetails}
        />
      </PageContainer>
    );
  }

  const documents = bidder.documents || [];

  const getDocStatusBadge = (status) => {
    switch (status) {
      case 'VERIFIED': return <Badge variant="success">Verified</Badge>;
      case 'UPLOADED': return <Badge variant="info">Uploaded</Badge>;
      case 'PENDING': return <Badge variant="warning">Pending</Badge>;
      case 'REJECTED': return <Badge variant="danger">Rejected</Badge>;
      default: return <Badge variant="neutral">{status}</Badge>;
    }
  };

  const getComplianceStatusBadge = (status) => {
    switch ((status || '').toUpperCase()) {
      case 'PASS': return <Badge variant="success">PASS</Badge>;
      case 'FAIL': return <Badge variant="danger">FAIL</Badge>;
      case 'PARTIAL': return <Badge variant="warning">PARTIAL</Badge>;
      case 'NOT_VERIFIED': return <Badge variant="neutral">NOT VERIFIED</Badge>;
      case 'NOT_APPLICABLE': return <Badge variant="info">NOT APPLICABLE</Badge>;
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

  const cardStyle = {
    backgroundColor: 'var(--color-bg-card)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    padding: 'var(--space-5)',
    boxShadow: 'var(--shadow-xs)',
  };

  const fieldStyle = {
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
  };

  const labelStyle = {
    fontSize: 'var(--font-size-xs)',
    color: 'var(--color-text-muted)',
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
  };

  const valueStyle = {
    fontSize: 'var(--font-size-sm)',
    color: 'var(--color-text-primary)',
    fontWeight: 'var(--font-weight-medium)',
  };

  const monoValueStyle = {
    ...valueStyle,
    fontFamily: 'var(--font-family-mono)',
    fontSize: 'var(--font-size-xs)',
    color: 'var(--color-text-secondary)',
  };

  return (
    <PageContainer
      title={bidder.name || bidder.legal_name}
      subtitle={bidder.registeredAddress || 'Registered Office, India'}
      actions={
        <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
          <Button variant="secondary" size="sm" onClick={() => navigate('/bidders')}>
            ← Back to Bidders
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => navigate(`/verification?bidder=${bidder.id}`)}
          >
            🛡 Start Verification
          </Button>
        </div>
      }
    >
      {/* Status & Tender reference */}
      <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap', alignItems: 'center' }}>
        {getBidderStatusBadge(bidder.status)}
        {getRiskBadge(bidder.risk)}
        <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
          Compliance Score:{' '}
          <strong
            style={{
              color: bidder.compliance >= 90 ? 'var(--color-success)' : bidder.compliance >= 70 ? 'var(--color-warning)' : 'var(--color-danger)',
            }}
          >
            {bidder.compliance != null ? `${bidder.compliance}%` : '—'}
          </strong>
        </span>
        {bidder.tenders && bidder.tenders.length > 1 ? (
          <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'center' }}>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>Tenders:</span>
            {bidder.tenders.map((t) => (
              <button
                key={t.id}
                type="button"
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--color-primary)',
                  cursor: 'pointer',
                  fontSize: 'var(--font-size-xs)',
                  padding: 0,
                  fontFamily: 'var(--font-family-mono)',
                }}
                onClick={() => navigate(`/tenders/${encodeURIComponent(t.reference_number || t.id)}`)}
              >
                ← {t.reference_number || t.id}
              </button>
            ))}
          </div>
        ) : bidder.tenderId ? (
          <button
            type="button"
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--color-primary)',
              cursor: 'pointer',
              fontSize: 'var(--font-size-xs)',
              padding: 0,
              fontFamily: 'var(--font-family-mono)',
            }}
            onClick={() => navigate(`/tenders/${encodeURIComponent(bidder.tenderId)}`)}
          >
            ← {bidder.tenderId}
          </button>
        ) : null}
      </div>

      {/* Statutory details */}
      <div style={cardStyle}>
        <h2 style={{ fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-primary)', marginBottom: 'var(--space-4)' }}>
          Statutory Details
        </h2>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: 'var(--space-4)',
          }}
        >
          <div style={fieldStyle}>
            <span style={labelStyle}>PAN</span>
            <span style={monoValueStyle}>{bidder.pan}</span>
          </div>
          <div style={fieldStyle}>
            <span style={labelStyle}>GSTIN</span>
            <span style={monoValueStyle}>{bidder.gstin || bidder.gst_number || 'N/A'}</span>
          </div>
          {bidder.udyam && (
            <div style={fieldStyle}>
              <span style={labelStyle}>Udyam Registration</span>
              <span style={monoValueStyle}>{bidder.udyam}</span>
            </div>
          )}
          <div style={fieldStyle}>
            <span style={labelStyle}>CIN</span>
            <span style={monoValueStyle}>{bidder.cin || bidder.registration_number || 'N/A'}</span>
          </div>
          <div style={fieldStyle}>
            <span style={labelStyle}>MSME Category</span>
            <span style={valueStyle}>{bidder.msmeCategory || 'NOT APPLICABLE'}</span>
          </div>
          <div style={fieldStyle}>
            <span style={labelStyle}>Annual Turnover</span>
            <span style={valueStyle}>{bidder.turnover || '—'}</span>
          </div>
          <div style={fieldStyle}>
            <span style={labelStyle}>Years in Business</span>
            <span style={valueStyle}>{bidder.yearsInBusiness ? `${bidder.yearsInBusiness} years` : '—'}</span>
          </div>
          <div style={fieldStyle}>
            <span style={labelStyle}>Contact Person</span>
            <span style={valueStyle}>{bidder.contactPerson || 'Authorized Signatory'}</span>
          </div>
          <div style={fieldStyle}>
            <span style={labelStyle}>Email</span>
            <span style={valueStyle}>{bidder.email || 'compliance@vendor.in'}</span>
          </div>
          <div style={fieldStyle}>
            <span style={labelStyle}>Phone</span>
            <span style={valueStyle}>{bidder.phone || '+91-11-23456789'}</span>
          </div>
        </div>
      </div>

      {/* Statutory Compliance Verification (Task 13 Multi-Source Orchestration) */}
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
            flexWrap: 'wrap',
            gap: 'var(--space-3)',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <h3 style={{ fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-primary)', margin: 0 }}>
                Multi-Source Statutory Compliance Pipeline
              </h3>
              <Badge variant="neutral">Task 13 Orchestration</Badge>
            </div>
            <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: '2px', marginBottom: 0 }}>
              Deterministic evaluation of approved tender requirements against multi-source evidence
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
            {evaluationsHistory.length > 0 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>Run:</span>
                <select
                  value={selectedEvalId || ''}
                  onChange={(e) => handleSelectEvaluation(e.target.value)}
                  disabled={evaluating || complianceLoading}
                  style={{
                    padding: '4px 8px',
                    fontSize: 'var(--font-size-xs)',
                    borderRadius: 'var(--radius-xs)',
                    border: '1px solid var(--color-border)',
                    backgroundColor: 'var(--color-bg-card)',
                    color: 'var(--color-text-primary)',
                  }}
                >
                  {evaluationsHistory.map((item, idx) => (
                    <option key={item.evaluation_id} value={item.evaluation_id}>
                      Run #{evaluationsHistory.length - idx} ({new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}) — {item.status}
                    </option>
                  ))}
                </select>
              </div>
            )}
            <Button
              variant="primary"
              size="sm"
              onClick={handleRunEvaluation}
              disabled={evaluating || complianceLoading}
            >
              {evaluating ? 'Evaluating…' : '↻ Run Compliance Evaluation'}
            </Button>
          </div>
        </div>

        {/* Disclaimer & Factual Notice */}
        <div
          style={{
            backgroundColor: 'var(--color-bg-subtle)',
            padding: 'var(--space-3) var(--space-5)',
            borderBottom: '1px solid var(--color-border-subtle)',
            fontSize: 'var(--font-size-xs)',
            color: 'var(--color-text-secondary)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-2)',
          }}
        >
          <span>⚖️</span>
          <span>
            <strong>Statutory Notice:</strong> Automated factual verification of individual requirements. Final procurement determinations remain strictly under human officer control.
          </span>
        </div>

        {/* Evaluation Error Banner (e.g. NO_APPROVED_REQUIREMENTS) */}
        {evalError && (
          <div
            style={{
              padding: 'var(--space-3) var(--space-5)',
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              borderBottom: '1px solid var(--color-danger)',
              color: 'var(--color-danger)',
              fontSize: 'var(--font-size-sm)',
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-2)',
            }}
          >
            <span>⚠️</span>
            <span>{evalError}</span>
          </div>
        )}

        {/* Compliance metrics overview */}
        {compliance && compliance.summary && (
          <div style={{ borderBottom: '1px solid var(--color-border-subtle)', backgroundColor: 'var(--color-bg-card)' }}>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
                gap: 'var(--space-3)',
                padding: 'var(--space-4) var(--space-5)',
              }}
            >
              <div style={{ textAlign: 'center', padding: 'var(--space-2)', backgroundColor: 'var(--color-bg-subtle)', borderRadius: 'var(--radius-sm)' }}>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Total Requirements</div>
                <div style={{ fontSize: 'var(--font-size-lg)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)' }}>
                  {compliance.summary.total_requirements}
                </div>
              </div>
              <div style={{ textAlign: 'center', padding: 'var(--space-2)', backgroundColor: 'var(--color-bg-subtle)', borderRadius: 'var(--radius-sm)' }}>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-success)', textTransform: 'uppercase' }}>Pass</div>
                <div style={{ fontSize: 'var(--font-size-lg)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-success)' }}>
                  {compliance.summary.pass_count}
                </div>
              </div>
              <div style={{ textAlign: 'center', padding: 'var(--space-2)', backgroundColor: 'var(--color-bg-subtle)', borderRadius: 'var(--radius-sm)' }}>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-danger)', textTransform: 'uppercase' }}>Fail</div>
                <div style={{ fontSize: 'var(--font-size-lg)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-danger)' }}>
                  {compliance.summary.fail_count}
                </div>
              </div>
              <div style={{ textAlign: 'center', padding: 'var(--space-2)', backgroundColor: 'var(--color-bg-subtle)', borderRadius: 'var(--radius-sm)' }}>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Not Verified</div>
                <div style={{ fontSize: 'var(--font-size-lg)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-secondary)' }}>
                  {compliance.summary.not_verified_count}
                </div>
              </div>
              <div style={{ textAlign: 'center', padding: 'var(--space-2)', backgroundColor: 'var(--color-bg-subtle)', borderRadius: 'var(--radius-sm)' }}>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-warning)', textTransform: 'uppercase' }}>Partial</div>
                <div style={{ fontSize: 'var(--font-size-lg)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-warning)' }}>
                  {compliance.summary.partial_count}
                </div>
              </div>
            </div>

            {/* Mandatory vs Optional Breakdown Sub-bar */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                padding: 'var(--space-2) var(--space-5)',
                backgroundColor: 'var(--color-bg-subtle)',
                fontSize: 'var(--font-size-xs)',
                color: 'var(--color-text-secondary)',
                flexWrap: 'wrap',
                gap: 'var(--space-2)',
              }}
            >
              <div>
                <strong>Mandatory ({compliance.summary.mandatory_total}):</strong>{' '}
                <span style={{ color: 'var(--color-success)' }}>{compliance.summary.mandatory_passed} Passed</span>,{' '}
                <span style={{ color: 'var(--color-danger)' }}>{compliance.summary.mandatory_failed} Failed</span>,{' '}
                <span style={{ color: 'var(--color-text-muted)' }}>{compliance.summary.mandatory_not_verified} Not Verified</span>
              </div>
              <div>
                <strong>Optional ({compliance.summary.optional_total}):</strong>{' '}
                <span style={{ color: 'var(--color-success)' }}>{compliance.summary.optional_passed} Passed</span>,{' '}
                <span style={{ color: 'var(--color-danger)' }}>{compliance.summary.optional_failed} Failed</span>,{' '}
                <span style={{ color: 'var(--color-text-muted)' }}>{compliance.summary.optional_not_verified} Not Verified</span>
              </div>
              {compliance.evaluation_id && (
                <div style={{ fontFamily: 'var(--font-family-mono)', color: 'var(--color-text-muted)' }}>
                  Run ID: {String(compliance.evaluation_id).slice(0, 8)}…
                </div>
              )}
            </div>
          </div>
        )}

        {/* Requirements list */}
        {complianceLoading ? (
          <div style={{ padding: 'var(--space-6)' }}>
            <Loading message="Running compliance pipeline..." size="sm" />
          </div>
        ) : !compliance || !compliance.requirements || compliance.requirements.length === 0 ? (
          <div style={{ padding: 'var(--space-6)', textAlign: 'center', color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>
            No compliance evaluation recorded yet.{' '}
            <button
              type="button"
              onClick={handleRunEvaluation}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--color-primary)',
                cursor: 'pointer',
                textDecoration: 'underline',
                padding: 0,
              }}
            >
              Run evaluation now
            </button>
          </div>
        ) : (
          <div style={{ padding: 'var(--space-4) var(--space-5)', display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
            {/* Status notice */}
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)', fontStyle: 'italic' }}>
              Compliance assessment completed. Click any requirement below to inspect multi-source traceable evidence.
            </div>

            {/* Render helper function inline */}
            {(() => {
              const reqs = compliance.requirements || [];
              const mandatoryList = reqs.filter((r) => r.mandatory);
              const optionalList = reqs.filter((r) => !r.mandatory);

              const renderRequirementCard = (req) => {
                const reqKey = req.requirement_id || req.requirement_code;
                const isExpanded = expandedReqs[reqKey] ?? true;

                // Detect AI-only vs unverified vs conflict
                const hasGovEvidence = (req.evidence || []).some((ev) => ev.verified || (ev.source && ev.source.includes('GOVERNMENT')));
                const hasAiEvidence = (req.evidence || []).some((ev) => ev.ai_extracted && Object.keys(ev.ai_extracted).length > 0);
                const hasConflict = (req.evidence || []).some((ev) => ev.conflict_detected);

                let notVerifiedMsg = 'Required verification evidence is unavailable.';
                if (req.status === 'NOT_VERIFIED') {
                  if (hasAiEvidence && !hasGovEvidence) {
                    notVerifiedMsg = 'Information was extracted from the submitted document, but required government verification is unavailable.';
                  } else {
                    notVerifiedMsg = 'Verification evidence unavailable.';
                  }
                }

                return (
                  <div
                    key={reqKey}
                    style={{
                      border: '1px solid var(--color-border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      padding: 'var(--space-4)',
                      backgroundColor: 'var(--color-bg-subtle)',
                      cursor: 'pointer',
                    }}
                    onClick={() => toggleReqExpand(reqKey)}
                  >
                    {/* Header */}
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-2)', marginBottom: 'var(--space-2)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                        <span style={{ fontFamily: 'var(--font-family-mono)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-primary)', fontSize: 'var(--font-size-sm)' }}>
                          {req.requirement_code}
                        </span>
                        <span style={{ fontWeight: 'var(--font-weight-medium)', color: 'var(--color-text-primary)', fontSize: 'var(--font-size-sm)' }}>
                          {req.requirement_title}
                        </span>
                        {req.mandatory ? <Badge variant="warning">Mandatory</Badge> : <Badge variant="neutral">Optional</Badge>}
                        {req.requirement_type && <Badge variant="neutral">{req.requirement_type}</Badge>}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            setInspectingReq(req);
                          }}
                        >
                          🔍 View Evidence
                        </Button>
                        {getComplianceStatusBadge(req.status)}
                        <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                          {isExpanded ? '▲' : '▼'}
                        </span>
                      </div>
                    </div>

                    {/* Explanation */}
                    {req.result?.summary && (
                      <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)', margin: 'var(--space-1) 0 var(--space-2) 0' }}>
                        {req.result.summary}
                      </p>
                    )}

                    {/* Special NOT_VERIFIED guidance */}
                    {req.status === 'NOT_VERIFIED' && (
                      <div
                        style={{
                          padding: 'var(--space-2) var(--space-3)',
                          backgroundColor: 'var(--color-bg-card)',
                          borderLeft: '3px solid var(--color-text-muted)',
                          borderRadius: 'var(--radius-xs)',
                          fontSize: 'var(--font-size-xs)',
                          color: 'var(--color-text-secondary)',
                          marginBottom: 'var(--space-2)',
                        }}
                      >
                        ℹ️ {notVerifiedMsg}
                      </div>
                    )}

                    {/* Evidence Conflict Alert */}
                    {hasConflict && (
                      <div
                        style={{
                          padding: 'var(--space-2) var(--space-3)',
                          backgroundColor: 'rgba(239, 68, 68, 0.1)',
                          borderLeft: '3px solid var(--color-danger)',
                          borderRadius: 'var(--radius-xs)',
                          fontSize: 'var(--font-size-xs)',
                          color: 'var(--color-danger)',
                          marginBottom: 'var(--space-2)',
                        }}
                      >
                        ⚠️ <strong>Evidence Conflict Detected:</strong> Government registry data differs from document AI extraction. Government-verified evidence took precedence. Both records are preserved below.
                      </div>
                    )}

                    {/* Expanded Detail View */}
                    {isExpanded && (
                      <div style={{ marginTop: 'var(--space-3)', borderTop: '1px solid var(--color-border-subtle)', paddingTop: 'var(--space-3)' }}>
                        {/* Rule-level breakdown */}
                        {req.rule_results && req.rule_results.length > 0 && (
                          <div style={{ marginBottom: 'var(--space-3)' }}>
                            <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-muted)', textTransform: 'uppercase', marginBottom: 'var(--space-1)' }}>
                              Rule Criteria Evaluation
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
                              {req.rule_results.map((rr, idx) => (
                                <div
                                  key={idx}
                                  style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'space-between',
                                    fontSize: 'var(--font-size-xs)',
                                    padding: 'var(--space-1) var(--space-2)',
                                    backgroundColor: 'var(--color-bg-card)',
                                    borderRadius: 'var(--radius-xs)',
                                  }}
                                >
                                  <span style={{ fontFamily: 'var(--font-family-mono)', color: 'var(--color-text-primary)' }}>
                                    {rr.field} ({rr.operator}): {rr.expected != null ? `expected "${rr.expected}", ` : ''}actual "{rr.actual ?? 'NONE'}"
                                  </span>
                                  <span>
                                    {rr.status === 'PASS' ? (
                                      <span style={{ color: 'var(--color-success)', fontWeight: 'var(--font-weight-bold)' }}>✓ PASS</span>
                                    ) : rr.status === 'FAIL' ? (
                                      <span style={{ color: 'var(--color-danger)', fontWeight: 'var(--font-weight-bold)' }}>✗ FAIL</span>
                                    ) : (
                                      <span style={{ color: 'var(--color-text-muted)' }}>— NOT VERIFIED</span>
                                    )}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Multi-Source Traceable Evidence links */}
                        {req.evidence && req.evidence.length > 0 && (
                          <div>
                            <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-muted)', textTransform: 'uppercase', marginBottom: 'var(--space-1)' }}>
                              Multi-Source Traceable Evidence
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                              {req.evidence.map((ev, i) => (
                                <div
                                  key={i}
                                  style={{
                                    padding: 'var(--space-2) var(--space-3)',
                                    backgroundColor: 'var(--color-bg-card)',
                                    border: '1px solid var(--color-border-subtle)',
                                    borderRadius: 'var(--radius-xs)',
                                    fontSize: 'var(--font-size-xs)',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    gap: '4px',
                                  }}
                                >
                                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                    <span>
                                      <strong>🏛 Source:</strong> {ev.source} ({ev.identifier || 'Identifier record'})
                                    </span>
                                    {ev.verified ? (
                                      <Badge variant="success">✓ Government Verified</Badge>
                                    ) : (
                                      <Badge variant="neutral">Document / AI Only</Badge>
                                    )}
                                  </div>

                                  {ev.government_data && Object.keys(ev.government_data).length > 0 && (
                                    <div style={{ fontFamily: 'var(--font-family-mono)', color: 'var(--color-text-secondary)', fontSize: '11px' }}>
                                      <strong>Government Registry:</strong> {JSON.stringify(ev.government_data)}
                                    </div>
                                  )}

                                  {ev.ai_extracted && Object.keys(ev.ai_extracted).length > 0 && (
                                    <div style={{ fontFamily: 'var(--font-family-mono)', color: 'var(--color-text-secondary)', fontSize: '11px' }}>
                                      <strong>Document AI Extracted:</strong> {JSON.stringify(ev.ai_extracted)}
                                    </div>
                                  )}

                                  {ev.document_id && (
                                    <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                                      Document ID: {ev.document_id}
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {req.evaluated_at && (
                          <div style={{ marginTop: 'var(--space-2)', fontSize: '10px', color: 'var(--color-text-muted)', textAlign: 'right' }}>
                            Evaluated at: {new Date(req.evaluated_at).toLocaleString()}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              };

              return (
                <>
                  {/* Mandatory Section */}
                  {mandatoryList.length > 0 && (
                    <div>
                      <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 'var(--space-2)' }}>
                        Mandatory Statutory Requirements ({mandatoryList.length})
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                        {mandatoryList.map(renderRequirementCard)}
                      </div>
                    </div>
                  )}

                  {/* Optional Section */}
                  {optionalList.length > 0 && (
                    <div>
                      <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 'var(--space-2)' }}>
                        Optional Statutory Requirements ({optionalList.length})
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                        {optionalList.map(renderRequirementCard)}
                      </div>
                    </div>
                  )}
                </>
              );
            })()}
          </div>
        )}
      </div>


      {/* Task 16 — Officer Review Section */}
      {selectedEvalId && compliance?.status === 'COMPLETED' && (
        <div
          style={{
            backgroundColor: 'var(--color-bg-card)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--color-border)',
            boxShadow: 'var(--shadow-xs)',
            overflow: 'hidden',
            marginTop: 'var(--space-4)',
          }}
        >
          {/* Section header */}
          <div
            style={{
              padding: 'var(--space-4) var(--space-5)',
              borderBottom: '1px solid var(--color-border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: 'var(--space-3)',
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <h3 style={{ fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-primary)', margin: 0 }}>
                  Officer Review
                </h3>
                <Badge variant="neutral">Task 16</Badge>
                {reviewPayload?.review?.status === 'COMPLETED' && <Badge variant="success">Completed</Badge>}
                {reviewPayload?.review?.status === 'IN_PROGRESS' && <Badge variant="info">In Progress</Badge>}
              </div>
              <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: 'var(--space-1)' }}>
                The system recommends and explains. The Procurement Officer decides.
              </p>
            </div>
            <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'center' }}>
              {!reviewPayload?.review && !reviewLoading && (
                <Button variant="primary" size="sm" onClick={handleStartReview} disabled={reviewLoading}>
                  📋 Start Officer Review
                </Button>
              )}
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setShowReview((v) => !v)}
              >
                {showReview ? 'Hide Review' : 'Show Review'}
              </Button>
            </div>
          </div>

          {showReview && (
            <div style={{ padding: 'var(--space-5)' }}>
              {reviewLoading ? (
                <Loading message="Loading review…" />
              ) : reviewPayload ? (
                <>
                  {/* Compliance summary */}
                  <ComplianceSummary
                    summary={reviewPayload.summary}
                    review={reviewPayload.review}
                  />

                  {/* Requirement-level reviews */}
                  {reviewPayload.review && (
                    <div style={{ marginBottom: '20px' }}>
                      <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 'var(--space-3)' }}>
                        Requirement Review ({reviewPayload.requirements?.length || 0})
                      </div>
                      {(reviewPayload.requirements || []).map((item) => (
                        <RequirementReview
                          key={item.requirement_result_id}
                          item={item}
                          onMarkReviewed={handleMarkReviewed}
                          onMarkFlagged={handleMarkFlagged}
                          onViewEvidence={(reqItem) => setInspectingReq({
                            ...reqItem,
                            requirement_id: reqItem.requirement_id,
                            title: reqItem.requirement_title,
                          })}
                          disabled={reviewPayload.review?.status === 'COMPLETED'}
                        />
                      ))}
                    </div>
                  )}

                  {/* Officer decision panel */}
                  {reviewPayload.review && (
                    <OfficerReviewPanel
                      review={reviewPayload.review}
                      onSaveDecision={handleSaveDecision}
                      onComplete={handleCompleteReview}
                      loading={reviewLoading}
                    />
                  )}
                </>
              ) : (
                <div style={{ padding: 'var(--space-4)', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                  No review started yet.
                  <br />
                  <Button variant="primary" size="sm" onClick={handleStartReview} style={{ marginTop: 'var(--space-3)' }}>
                    Start Officer Review
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>
      )}


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
          <div>
            <h3 style={{ fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-primary)' }}>
              Submitted Documents
            </h3>
            <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
              Statutory and supporting compliance documentation
            </p>
          </div>
          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
            {documents.length} documents
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
                <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Filename</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Status</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Verified By</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Upload Date</th>
                <th style={{ padding: 'var(--space-3) var(--space-5)', textAlign: 'right' }}>Size</th>
              </tr>
            </thead>
            <tbody>
              {documents.length === 0 ? (
                <tr>
                  <td
                    colSpan="6"
                    style={{
                      padding: 'var(--space-6)',
                      textAlign: 'center',
                      color: 'var(--color-text-muted)',
                      fontSize: 'var(--font-size-sm)',
                    }}
                  >
                    No compliance documents submitted yet.
                  </td>
                </tr>
              ) : (
                documents.map((doc, index) => (
                  <tr
                    key={doc.id}
                    style={{
                      borderBottom: index === documents.length - 1 ? 'none' : '1px solid var(--color-border-subtle)',
                      transition: 'background-color var(--transition-fast)',
                    }}
                    onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'var(--color-bg-hover)'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; }}
                  >
                    <td style={{ padding: 'var(--space-3) var(--space-5)', fontWeight: 'var(--font-weight-medium)', color: 'var(--color-text-primary)' }}>
                      {doc.type}
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
                    <td style={{ padding: 'var(--space-3) var(--space-5)', textAlign: 'right', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                      {doc.size}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Verification CTA */}
      <div
        style={{
          backgroundColor: 'var(--color-bg-card)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-5)',
          boxShadow: 'var(--shadow-xs)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 'var(--space-4)',
        }}
      >
        <div>
          <h3 style={{ fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-primary)' }}>
            Ready to verify this vendor?
          </h3>
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', marginTop: 'var(--space-1)' }}>
            Run the SecondLook verification pipeline to check PAN, GST, Udyam, EPFO, MCA, and blacklist registries.
          </p>
        </div>
        <Button
          variant="success"
          size="lg"
          onClick={() => navigate(`/verification?bidder=${bidder.id}`)}
        >
          🛡 Start Verification →
        </Button>
      </div>

      <EvidenceTraceModal
        isOpen={!!inspectingReq}
        onClose={() => setInspectingReq(null)}
        requirement={inspectingReq}
        evaluationId={selectedEvalId}
        bidderId={bidderId}
      />
    </PageContainer>
  );
}
