import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import PageContainer from '../components/layout/PageContainer.jsx';
import Badge from '../components/common/Badge.jsx';
import Button from '../components/common/Button.jsx';
import Loading from '../components/common/Loading.jsx';
import EmptyState from '../components/common/EmptyState.jsx';
import { getAllBidders, getBidderById, getVerificationResult } from '../data/demoData.js';

/**
 * VerificationPage — M20
 * Interactive demo verification runner:
 *   Select Bidder → Start → Animated Processing → Results → Officer Decision
 *
 * All results are deterministic demo data — no real APIs are called.
 */

const STEP_DELAY_MS = 480; // ms between pipeline log steps

// ─── States ───────────────────────────────────────────────────────────────────
const STATE = {
  SELECT: 'SELECT',
  RUNNING: 'RUNNING',
  COMPLETE: 'COMPLETE',
};

export default function VerificationPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const bidderId = searchParams.get('bidder');

  const [selectedBidderId, setSelectedBidderId] = useState(bidderId || '');
  const [pageState, setPageState] = useState(STATE.SELECT);
  const [completedSteps, setCompletedSteps] = useState([]);
  const [officerDecision, setOfficerDecision] = useState(null); // null | 'APPROVED' | 'REJECTED' | 'CLARIFICATION'
  const [inspectingSource, setInspectingSource] = useState(null); // null | object
  const intervalRef = useRef(null);

  const allBidders = getAllBidders();
  const selectedBidder = selectedBidderId ? getBidderById(selectedBidderId) : null;
  const result = selectedBidderId ? getVerificationResult(selectedBidderId) : null;

  // Auto-select from query param
  useEffect(() => {
    if (bidderId) setSelectedBidderId(bidderId);
  }, [bidderId]);

  // Cleanup on unmount
  useEffect(() => {
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, []);

  function startVerification() {
    if (!result) return;
    setPageState(STATE.RUNNING);
    setCompletedSteps([]);
    setOfficerDecision(null);

    let stepIndex = 0;
    intervalRef.current = setInterval(() => {
      stepIndex += 1;
      setCompletedSteps((prev) => [...prev, result.processingSteps[stepIndex - 1]]);
      if (stepIndex >= result.processingSteps.length) {
        clearInterval(intervalRef.current);
        setTimeout(() => setPageState(STATE.COMPLETE), 400);
      }
    }, STEP_DELAY_MS);
  }

  function resetVerification() {
    if (intervalRef.current) clearInterval(intervalRef.current);
    setPageState(STATE.SELECT);
    setCompletedSteps([]);
    setOfficerDecision(null);
  }

  // ─── Rendering helpers ──────────────────────────────────────────────────────

  const getRiskBadge = (risk) => {
    switch (risk) {
      case 'LOW': return <Badge variant="success">✓ Low Risk</Badge>;
      case 'MEDIUM': return <Badge variant="warning">⚠ Medium Risk</Badge>;
      case 'HIGH': return <Badge variant="danger">✗ High Risk</Badge>;
      default: return <Badge variant="neutral">{risk}</Badge>;
    }
  };

  const getSourceStatusBadge = (status) => {
    switch (status) {
      case 'VERIFIED': return <Badge variant="success">Verified</Badge>;
      case 'CLEAR': return <Badge variant="success">Clear</Badge>;
      case 'PENDING': return <Badge variant="warning">Pending</Badge>;
      case 'WARNING': return <Badge variant="warning">Warning</Badge>;
      case 'FAILED': return <Badge variant="danger">Failed</Badge>;
      default: return <Badge variant="neutral">{status}</Badge>;
    }
  };

  const getFindingIcon = (status) => {
    switch (status) {
      case 'PASS': return { icon: '✓', color: 'var(--color-success)' };
      case 'WARN': return { icon: '⚠', color: 'var(--color-warning)' };
      case 'FAIL': return { icon: '✗', color: 'var(--color-danger)' };
      default: return { icon: '–', color: 'var(--color-text-muted)' };
    }
  };

  const cardStyle = {
    backgroundColor: 'var(--color-bg-card)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    padding: 'var(--space-5)',
    boxShadow: 'var(--shadow-xs)',
  };

  const sectionTitle = (text) => (
    <h2
      style={{
        fontSize: 'var(--font-size-base)',
        fontWeight: 'var(--font-weight-semibold)',
        color: 'var(--color-text-primary)',
        marginBottom: 'var(--space-4)',
      }}
    >
      {text}
    </h2>
  );

  // ─── Page States ────────────────────────────────────────────────────────────

  // STATE: SELECT
  if (pageState === STATE.SELECT) {
    return (
      <PageContainer
        title="Verification"
        subtitle="Run the SecondLook compliance pipeline against a registered vendor"
      >
        <div style={cardStyle}>
          {sectionTitle('Select a Vendor to Verify')}
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', marginBottom: 'var(--space-5)' }}>
            Choose a vendor from the list below. The SecondLook pipeline will check PAN, GST, Udyam, EPFO, MCA21, and central blacklist registries using demo data.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)', marginBottom: 'var(--space-5)' }}>
            {allBidders.map((bidder) => {
              const isSelected = selectedBidderId === bidder.id;
              return (
                <button
                  key={bidder.id}
                  type="button"
                  onClick={() => setSelectedBidderId(bidder.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: 'var(--space-3) var(--space-4)',
                    borderRadius: 'var(--radius-sm)',
                    border: `2px solid ${isSelected ? 'var(--color-primary)' : 'var(--color-border)'}`,
                    backgroundColor: isSelected ? 'var(--color-primary-subtle)' : 'var(--color-bg-page)',
                    cursor: 'pointer',
                    textAlign: 'left',
                    transition: 'border-color var(--transition-fast), background-color var(--transition-fast)',
                    flexWrap: 'wrap',
                    gap: 'var(--space-2)',
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 'var(--font-weight-medium)', color: isSelected ? 'var(--color-primary)' : 'var(--color-text-primary)', fontSize: 'var(--font-size-sm)' }}>
                      {bidder.name}
                    </div>
                    <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: '2px', fontFamily: 'var(--font-family-mono)' }}>
                      PAN: {bidder.pan} · GSTIN: {bidder.gstin}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
                    {bidder.risk === 'HIGH' ? (
                      <Badge variant="danger">High Risk</Badge>
                    ) : bidder.risk === 'MEDIUM' ? (
                      <Badge variant="warning">Med Risk</Badge>
                    ) : (
                      <Badge variant="success">Low Risk</Badge>
                    )}
                    {bidder.status === 'VERIFIED' && <Badge variant="success">Verified</Badge>}
                    {bidder.status === 'FLAGGED' && <Badge variant="danger">Flagged</Badge>}
                  </div>
                </button>
              );
            })}
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--space-3)', paddingTop: 'var(--space-4)', borderTop: '1px solid var(--color-border-subtle)' }}>
            <Button variant="secondary" onClick={() => navigate('/bidders')}>
              Browse Vendors
            </Button>
            <Button
              variant="success"
              size="lg"
              disabled={!selectedBidderId}
              onClick={startVerification}
            >
              🛡 Start Verification
            </Button>
          </div>
        </div>
      </PageContainer>
    );
  }

  // STATE: RUNNING
  if (pageState === STATE.RUNNING) {
    return (
      <PageContainer
        title="Verification"
        subtitle={`Running pipeline for: ${selectedBidder?.name ?? selectedBidderId}`}
      >
        <div style={cardStyle}>
          <div style={{ textAlign: 'center', padding: 'var(--space-6) 0' }}>
            <Loading size="lg" message="Verification pipeline running..." />
          </div>

          <div
            style={{
              backgroundColor: 'var(--color-bg-page)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-sm)',
              padding: 'var(--space-4)',
              fontFamily: 'var(--font-family-mono)',
              fontSize: 'var(--font-size-xs)',
              lineHeight: 1.8,
              maxHeight: '280px',
              overflowY: 'auto',
              marginTop: 'var(--space-4)',
            }}
          >
            {completedSteps.map((step, i) => (
              <div key={i} style={{ color: 'var(--color-text-secondary)' }}>
                <span style={{ color: 'var(--color-success)', marginRight: 'var(--space-2)' }}>✓</span>
                {step}
              </div>
            ))}
            {completedSteps.length < (result?.processingSteps?.length ?? 0) && (
              <div style={{ color: 'var(--color-primary)' }}>
                <span style={{ marginRight: 'var(--space-2)' }}>▶</span>
                {result?.processingSteps[completedSteps.length]}
              </div>
            )}
          </div>

          <div style={{ textAlign: 'right', marginTop: 'var(--space-4)' }}>
            <Button variant="secondary" size="sm" onClick={resetVerification}>
              Cancel
            </Button>
          </div>
        </div>
      </PageContainer>
    );
  }

  // STATE: COMPLETE
  if (!result) {
    return (
      <PageContainer title="Verification">
        <EmptyState
          title="No verification data"
          description="No demo verification result is available for this vendor."
          actionLabel="Select another vendor"
          onAction={resetVerification}
        />
      </PageContainer>
    );
  }

  const scoreColor =
    result.score >= 85 ? 'var(--color-success)' :
    result.score >= 65 ? 'var(--color-warning)' :
    'var(--color-danger)';

  return (
    <PageContainer
      title="Verification Result"
      subtitle={`${result.bidderName} · ${result.verificationDate}`}
      actions={
        <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
          <Button variant="secondary" size="sm" onClick={resetVerification}>
            ← New Verification
          </Button>
          <Button variant="ghost" size="sm" onClick={() => navigate(`/bidders/${result.bidderId}`)}>
            View Bidder Profile
          </Button>
        </div>
      }
    >
      {/* Score + Risk header row */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 'var(--space-4)',
        }}
      >
        {/* Compliance Score */}
        <div
          style={{
            ...cardStyle,
            textAlign: 'center',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 'var(--space-2)',
          }}
        >
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Compliance Score
          </div>
          <div
            style={{
              fontSize: '3rem',
              fontWeight: 'var(--font-weight-bold)',
              color: scoreColor,
              lineHeight: 1,
            }}
          >
            {result.score}
          </div>
          <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>
            out of {result.maxScore}
          </div>
          <div
            role="progressbar"
            aria-valuenow={result.score}
            aria-valuemin={0}
            aria-valuemax={100}
            style={{
              width: '100%',
              height: '8px',
              borderRadius: 'var(--radius-full)',
              backgroundColor: 'var(--color-bg-subtle)',
              overflow: 'hidden',
              marginTop: 'var(--space-2)',
            }}
          >
            <div
              style={{
                width: `${result.score}%`,
                height: '100%',
                backgroundColor: scoreColor,
                borderRadius: 'var(--radius-full)',
                transition: 'width 0.6s ease',
              }}
            />
          </div>
        </div>

        {/* Risk Level */}
        <div
          style={{
            ...cardStyle,
            textAlign: 'center',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 'var(--space-3)',
          }}
        >
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Risk Classification
          </div>
          <div style={{ transform: 'scale(1.4)', transformOrigin: 'center' }}>
            {getRiskBadge(result.risk)}
          </div>
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
            {result.risk === 'LOW' && 'All statutory checks passed. Vendor is compliant.'}
            {result.risk === 'MEDIUM' && 'Minor issues found. Review recommended before approval.'}
            {result.risk === 'HIGH' && 'Critical non-compliance detected. Manual review required.'}
          </div>
        </div>

        {/* Provider Info */}
        <div
          style={{
            ...cardStyle,
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-3)',
            justifyContent: 'center',
          }}
        >
          <div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Pipeline</div>
            <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)', fontWeight: 'var(--font-weight-medium)' }}>{result.provider}</div>
          </div>
          <div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Vendor</div>
            <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)', fontWeight: 'var(--font-weight-medium)' }}>{result.bidderName}</div>
          </div>
          <div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Date</div>
            <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)', fontWeight: 'var(--font-weight-medium)' }}>{result.verificationDate}</div>
          </div>
        </div>
      </div>

      {/* Findings */}
      <div style={cardStyle}>
        {sectionTitle('Verification Findings')}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
          {result.findings.map((finding, i) => {
            const { icon, color } = getFindingIcon(finding.status);
            return (
              <div
                key={i}
                style={{
                  display: 'flex',
                  gap: 'var(--space-4)',
                  padding: 'var(--space-3) var(--space-4)',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: 'var(--color-bg-page)',
                  border: '1px solid var(--color-border-subtle)',
                  alignItems: 'flex-start',
                }}
              >
                <span style={{ fontSize: 'var(--font-size-base)', color, fontWeight: 'var(--font-weight-bold)', flexShrink: 0, width: '16px', textAlign: 'center' }}>
                  {icon}
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 'var(--font-weight-semibold)', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)' }}>
                    {finding.check}
                  </div>
                  <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)', marginTop: '2px', lineHeight: 1.5 }}>
                    {finding.detail}
                  </div>
                </div>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', flexShrink: 0, textAlign: 'right' }}>
                  {finding.source}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Evidence Sources (Task 14 Multi-Source Government Verification) */}
      <div
        style={{
          backgroundColor: 'var(--color-bg-card)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--color-border)',
          boxShadow: 'var(--shadow-xs)',
          overflow: 'hidden',
        }}
      >
        <div style={{ padding: 'var(--space-4) var(--space-5)', borderBottom: '1px solid var(--color-border)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
            <div>
              <h2 style={{ fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-primary)' }}>
                Statutory Evidence Sources (Multi-Source Verification)
              </h2>
              <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: '2px' }}>
                Normalized statutory verification adapters across 10 central registries. All sources operating in deterministic DEMO mode.
              </p>
            </div>
            <Badge variant="neutral">Task 14 Multi-Source</Badge>
          </div>
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
                <th style={{ padding: 'var(--space-3) var(--space-5)' }}>Registry / Source</th>
                <th style={{ padding: 'var(--space-3) var(--space-3)', textAlign: 'center' }}>Mode</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Identifier / Entity</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Status</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'right' }}>Response Time</th>
                <th style={{ padding: 'var(--space-3) var(--space-5)', textAlign: 'center' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {result.evidenceSources.map((src, index) => (
                <tr
                  key={src.code || src.source}
                  style={{
                    borderBottom: index === result.evidenceSources.length - 1 ? 'none' : '1px solid var(--color-border-subtle)',
                  }}
                >
                  <td style={{ padding: 'var(--space-3) var(--space-5)', fontWeight: 'var(--font-weight-medium)', color: 'var(--color-text-primary)', fontSize: 'var(--font-size-sm)' }}>
                    <div>{src.source}</div>
                    {src.provider && (
                      <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', fontFamily: 'var(--font-family-mono)', marginTop: '2px' }}>
                        {src.provider}
                      </div>
                    )}
                  </td>
                  <td style={{ padding: 'var(--space-3) var(--space-3)', textAlign: 'center' }}>
                    <span
                      style={{
                        fontSize: '10px',
                        fontWeight: 'var(--font-weight-bold)',
                        letterSpacing: '0.06em',
                        padding: '2px 6px',
                        borderRadius: 'var(--radius-xs)',
                        backgroundColor: 'var(--color-primary-subtle)',
                        color: 'var(--color-primary)',
                        border: '1px solid var(--color-primary)',
                      }}
                    >
                      DEMO
                    </span>
                  </td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)', fontFamily: 'var(--font-family-mono)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                    {src.identifier || '—'}
                  </td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                    {getSourceStatusBadge(src.status)}
                  </td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'right', fontFamily: 'var(--font-family-mono)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                    {src.responseTime}
                  </td>
                  <td style={{ padding: 'var(--space-3) var(--space-5)', textAlign: 'center' }}>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setInspectingSource(src)}
                    >
                      Inspect
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Verification Data Inspection Modal */}
      {inspectingSource && (
        <div
          role="dialog"
          aria-modal="true"
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.55)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: 'var(--space-4)',
          }}
          onClick={() => setInspectingSource(null)}
        >
          <div
            style={{
              backgroundColor: 'var(--color-bg-card)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-border)',
              maxWidth: '560px',
              width: '100%',
              padding: 'var(--space-5)',
              boxShadow: 'var(--shadow-lg)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-4)' }}>
              <div>
                <h3 style={{ fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-primary)' }}>
                  {inspectingSource.source}
                </h3>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginTop: 'var(--space-1)' }}>
                  <span style={{ fontSize: '10px', fontWeight: 'bold', padding: '1px 5px', borderRadius: '3px', backgroundColor: 'var(--color-primary-subtle)', color: 'var(--color-primary)', border: '1px solid var(--color-primary)' }}>
                    DEMO PROVIDER
                  </span>
                  <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', fontFamily: 'var(--font-family-mono)' }}>
                    {inspectingSource.provider || 'Demo Provider'}
                  </span>
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setInspectingSource(null)}>
                ✕
              </Button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)', marginBottom: 'var(--space-4)', fontSize: 'var(--font-size-xs)' }}>
              <div>
                <div style={{ color: 'var(--color-text-muted)' }}>Identifier Queried</div>
                <div style={{ fontWeight: 'var(--font-weight-semibold)', fontFamily: 'var(--font-family-mono)', color: 'var(--color-text-primary)' }}>
                  {inspectingSource.identifier || 'N/A'}
                </div>
              </div>
              <div>
                <div style={{ color: 'var(--color-text-muted)' }}>Verification Status</div>
                <div>{getSourceStatusBadge(inspectingSource.status)}</div>
              </div>
              <div>
                <div style={{ color: 'var(--color-text-muted)' }}>Retrieved Timestamp</div>
                <div style={{ fontFamily: 'var(--font-family-mono)', color: 'var(--color-text-secondary)' }}>
                  {inspectingSource.retrievedAt || new Date().toISOString()}
                </div>
              </div>
              <div>
                <div style={{ color: 'var(--color-text-muted)' }}>Mode</div>
                <div style={{ color: 'var(--color-text-secondary)' }}>Offline Synthetic Record</div>
              </div>
            </div>

            <div style={{ marginBottom: 'var(--space-4)' }}>
              <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 'var(--font-weight-medium)', color: 'var(--color-text-muted)', marginBottom: 'var(--space-1)' }}>
                Normalized Statutory Payload:
              </div>
              <pre
                style={{
                  backgroundColor: 'var(--color-bg-page)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-sm)',
                  padding: 'var(--space-3)',
                  fontSize: 'var(--font-size-xs)',
                  fontFamily: 'var(--font-family-mono)',
                  color: 'var(--color-text-primary)',
                  overflowX: 'auto',
                  maxHeight: '180px',
                  margin: 0,
                }}
              >
                {JSON.stringify(inspectingSource.data || { status: inspectingSource.status, source: inspectingSource.source }, null, 2)}
              </pre>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button variant="secondary" size="sm" onClick={() => setInspectingSource(null)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Officer Decision — Demo Only */}
      <div
        style={{
          ...cardStyle,
          borderLeft: `4px solid ${officerDecision === 'APPROVED' ? 'var(--color-success)' : officerDecision === 'REJECTED' ? 'var(--color-danger)' : officerDecision === 'CLARIFICATION' ? 'var(--color-warning)' : 'var(--color-border)'}`,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-3)', marginBottom: 'var(--space-4)' }}>
          <div>
            <h2 style={{ fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-primary)' }}>
              Officer Decision
            </h2>
            <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: 'var(--space-1)' }}>
              Demo UI only — no RBAC, authentication, or legal approval workflow
            </p>
          </div>
          {officerDecision && (
            <div>
              {officerDecision === 'APPROVED' && <Badge variant="success">✓ Decision Recorded: Approved</Badge>}
              {officerDecision === 'REJECTED' && <Badge variant="danger">✗ Decision Recorded: Rejected</Badge>}
              {officerDecision === 'CLARIFICATION' && <Badge variant="warning">⚠ Clarification Requested</Badge>}
            </div>
          )}
        </div>

        {officerDecision ? (
          <div
            style={{
              padding: 'var(--space-4)',
              backgroundColor: 'var(--color-bg-page)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border-subtle)',
              fontSize: 'var(--font-size-sm)',
              color: 'var(--color-text-secondary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: 'var(--space-3)',
            }}
          >
            <span>
              Decision recorded by <strong style={{ color: 'var(--color-text-primary)' }}>Auditor Officer</strong> on{' '}
              {result.verificationDate} · Ref: {result.bidderId}
            </span>
            <Button variant="ghost" size="sm" onClick={() => setOfficerDecision(null)}>
              Revise
            </Button>
          </div>
        ) : (
          <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
            <Button
              variant="success"
              size="md"
              onClick={() => setOfficerDecision('APPROVED')}
            >
              ✓ Approve
            </Button>
            <Button
              variant="danger"
              size="md"
              onClick={() => setOfficerDecision('REJECTED')}
            >
              ✗ Reject
            </Button>
            <Button
              variant="warning"
              size="md"
              onClick={() => setOfficerDecision('CLARIFICATION')}
            >
              ⚠ Request Clarification
            </Button>
          </div>
        )}
      </div>
    </PageContainer>
  );
}
