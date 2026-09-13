import React, { useState, useEffect } from 'react';
import Modal from '../common/Modal.jsx';
import Badge from '../common/Badge.jsx';
import Button from '../common/Button.jsx';
import Loading from '../common/Loading.jsx';
import {
  getRequirementEvidenceTrace,
  getDocumentAccessUrl,
} from '../../services/complianceService.js';

export default function EvidenceTraceModal({
  isOpen,
  onClose,
  requirement,
  evaluationId,
  bidderId,
}) {
  const [trace, setTrace] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showOcrText, setShowOcrText] = useState(false);
  const [accessLoading, setAccessLoading] = useState(false);
  const [accessError, setAccessError] = useState(null);

  useEffect(() => {
    if (!isOpen || !requirement) {
      setTrace(null);
      setShowOcrText(false);
      setError(null);
      return;
    }

    const fetchTrace = async () => {
      setLoading(true);
      setError(null);
      try {
        const reqId = requirement.requirement_id || requirement.id;
        const data = await getRequirementEvidenceTrace(reqId, bidderId);
        setTrace(data);
      } catch (err) {
        console.error('Failed to load requirement trace:', err);
        setError('Unable to load detailed evidence trace. Displaying cached evaluation data.');
      } finally {
        setLoading(false);
      }
    };

    fetchTrace();
  }, [isOpen, requirement, bidderId]);

  const handleViewDocument = async (documentId) => {
    if (!documentId) return;
    setAccessLoading(true);
    setAccessError(null);
    try {
      const accessData = await getDocumentAccessUrl(documentId);
      if (accessData?.download_url) {
        window.open(accessData.download_url, '_blank', 'noopener,noreferrer');
      } else {
        setAccessError('No access URL generated for this document.');
      }
    } catch (err) {
      console.error('Failed to generate document access URL:', err);
      setAccessError('Unable to generate secure document access URL.');
    } finally {
      setAccessLoading(false);
    }
  };

  if (!isOpen || !requirement) return null;

  const reqCode = requirement.requirement_code || trace?.requirement_code || 'REQ';
  const reqTitle = requirement.requirement_title || trace?.requirement_title || 'Statutory Requirement';
  const status = requirement.status || trace?.evaluation_status || 'NOT_VERIFIED';
  const isMandatory = requirement.mandatory !== false;

  const getStatusBadge = (st) => {
    switch (st) {
      case 'PASS':
        return <Badge variant="success">✓ PASS</Badge>;
      case 'FAIL':
        return <Badge variant="danger">✗ FAIL</Badge>;
      case 'PARTIAL':
        return <Badge variant="warning">PARTIAL</Badge>;
      default:
        return <Badge variant="neutral">NOT VERIFIED</Badge>;
    }
  };

  const evidenceItems = trace?.evidence_items?.length ? trace.evidence_items : (requirement.evidence || []);
  const docTrace = trace?.document_trace;
  const ocrTrace = trace?.ocr_trace;
  const aiTrace = trace?.ai_trace;
  const govTrace = trace?.government_trace;
  const ruleResults = trace?.rule_results?.length ? trace.rule_results : (requirement.rule_results || []);

  // Collect field comparisons across evidence items
  const fieldComparisons = [];
  evidenceItems.forEach((ev) => {
    if (ev.field_comparisons && Array.isArray(ev.field_comparisons)) {
      fieldComparisons.push(...ev.field_comparisons);
    }
  });

  const docId = docTrace?.document_id || evidenceItems.find((e) => e.document_id)?.document_id;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <span style={{ fontFamily: 'var(--font-family-mono)', color: 'var(--color-primary)' }}>{reqCode}</span>
          <span>Traceable Evidence Inspection</span>
        </div>
      }
      maxWidth="850px"
      footer={
        <Button variant="secondary" size="sm" onClick={onClose}>
          Close
        </Button>
      }
    >
      <div style={{ maxHeight: '75vh', overflowY: 'auto', paddingRight: 'var(--space-2)', display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
        {/* Header Summary */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-2)', padding: 'var(--space-3)', backgroundColor: 'var(--color-bg-subtle)', borderRadius: 'var(--radius-sm)' }}>
          <div>
            <div style={{ fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-primary)' }}>
              {reqTitle}
            </div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
              {isMandatory ? 'Mandatory Statutory Requirement' : 'Optional Requirement'}
              {evaluationId && ` • Evaluation ID: ${evaluationId.slice(0, 8)}…`}
            </div>
          </div>
          <div>{getStatusBadge(status)}</div>
        </div>

        {loading && <Loading message="Loading full evidence trace..." size="sm" />}

        {error && (
          <div style={{ padding: 'var(--space-2) var(--space-3)', backgroundColor: 'rgba(234, 179, 8, 0.1)', color: 'var(--color-warning)', borderRadius: 'var(--radius-xs)', fontSize: 'var(--font-size-xs)' }}>
            ⚠️ {error}
          </div>
        )}

        {/* Deterministic Explanation */}
        <div style={{ border: '1px solid var(--color-border-subtle)', borderRadius: 'var(--radius-sm)', padding: 'var(--space-3)', backgroundColor: 'var(--color-bg-card)' }}>
          <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-muted)', textTransform: 'uppercase', marginBottom: 'var(--space-1)' }}>
            Deterministic Compliance Explanation
          </div>
          <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)', whiteSpace: 'pre-wrap', lineHeight: 1.5 }}>
            {trace?.explanation || requirement.result?.explanation || requirement.result?.summary || 'No explanation recorded.'}
          </div>
        </div>

        {/* Rule Criteria Evaluation */}
        {ruleResults.length > 0 && (
          <div style={{ border: '1px solid var(--color-border-subtle)', borderRadius: 'var(--radius-sm)', padding: 'var(--space-3)', backgroundColor: 'var(--color-bg-card)' }}>
            <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-muted)', textTransform: 'uppercase', marginBottom: 'var(--space-2)' }}>
              Rule Criteria Evaluation
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
              {ruleResults.map((rr, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: 'var(--space-2) var(--space-3)',
                    backgroundColor: 'var(--color-bg-subtle)',
                    borderRadius: 'var(--radius-xs)',
                    fontSize: 'var(--font-size-xs)',
                  }}
                >
                  <div>
                    <span style={{ fontFamily: 'var(--font-family-mono)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-primary)' }}>
                      {rr.field}
                    </span>
                    <span style={{ color: 'var(--color-text-muted)', margin: '0 var(--space-2)' }}>|</span>
                    <span style={{ color: 'var(--color-text-secondary)' }}>
                      Operator: <strong>{rr.operator}</strong> • Expected: "{String(rr.expected ?? '')}" • Actual: "{String(rr.actual ?? 'NONE')}"
                    </span>
                  </div>
                  <div>
                    {rr.status === 'PASS' ? (
                      <span style={{ color: 'var(--color-success)', fontWeight: 'bold' }}>✓ PASS</span>
                    ) : rr.status === 'FAIL' ? (
                      <span style={{ color: 'var(--color-danger)', fontWeight: 'bold' }}>✗ FAIL</span>
                    ) : (
                      <span style={{ color: 'var(--color-text-muted)' }}>— NOT VERIFIED</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Side-by-side Field Comparison Table */}
        {fieldComparisons.length > 0 && (
          <div style={{ border: '1px solid var(--color-border-subtle)', borderRadius: 'var(--radius-sm)', padding: 'var(--space-3)', backgroundColor: 'var(--color-bg-card)' }}>
            <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-muted)', textTransform: 'uppercase', marginBottom: 'var(--space-2)' }}>
              Side-by-Side Field Comparison
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--font-size-xs)' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--color-border)', color: 'var(--color-text-secondary)', textAlign: 'left' }}>
                    <th style={{ padding: 'var(--space-2)' }}>Field</th>
                    <th style={{ padding: 'var(--space-2)' }}>Tender Expected</th>
                    <th style={{ padding: 'var(--space-2)' }}>Document AI Extracted</th>
                    <th style={{ padding: 'var(--space-2)' }}>Government Registry Record</th>
                    <th style={{ padding: 'var(--space-2)' }}>Comparison</th>
                  </tr>
                </thead>
                <tbody>
                  {fieldComparisons.map((fc, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                      <td style={{ padding: 'var(--space-2)', fontFamily: 'var(--font-family-mono)', fontWeight: 'var(--font-weight-medium)' }}>
                        {fc.field}
                      </td>
                      <td style={{ padding: 'var(--space-2)', color: 'var(--color-text-secondary)' }}>
                        {fc.expected_value != null ? String(fc.expected_value) : '—'}
                      </td>
                      <td style={{ padding: 'var(--space-2)', color: 'var(--color-text-primary)' }}>
                        {fc.document_value != null ? String(fc.document_value) : '—'}
                      </td>
                      <td style={{ padding: 'var(--space-2)', color: 'var(--color-text-primary)' }}>
                        {fc.government_value != null ? String(fc.government_value) : '—'}
                      </td>
                      <td style={{ padding: 'var(--space-2)' }}>
                        {fc.result === 'MATCH' ? (
                          <Badge variant="success">✓ MATCH</Badge>
                        ) : fc.result === 'MISMATCH' ? (
                          <Badge variant="danger">✗ MISMATCH</Badge>
                        ) : (
                          <Badge variant="neutral">UNAVAILABLE</Badge>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Attached Document & Secure File Access */}
        <div style={{ border: '1px solid var(--color-border-subtle)', borderRadius: 'var(--radius-sm)', padding: 'var(--space-3)', backgroundColor: 'var(--color-bg-card)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-2)' }}>
            <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
              Attached Bidder Document
            </div>
            {docId && (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => handleViewDocument(docId)}
                disabled={accessLoading}
              >
                {accessLoading ? 'Generating Link...' : '📄 View Document (Signed URL)'}
              </Button>
            )}
          </div>

          {accessError && (
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-danger)', marginBottom: 'var(--space-2)' }}>
              ⚠️ {accessError}
            </div>
          )}

          {docTrace ? (
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--space-2)', backgroundColor: 'var(--color-bg-subtle)', padding: 'var(--space-2) var(--space-3)', borderRadius: 'var(--radius-xs)' }}>
              <div><strong>File:</strong> {docTrace.file_name}</div>
              <div><strong>Type:</strong> {docTrace.document_type || 'DOCUMENT'}</div>
              <div><strong>Size:</strong> {docTrace.file_size ? `${Math.round(docTrace.file_size / 1024)} KB` : '—'}</div>
              <div><strong>Uploaded:</strong> {docTrace.uploaded_at ? new Date(docTrace.uploaded_at).toLocaleString() : '—'}</div>
            </div>
          ) : docId ? (
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
              Document ID: <code style={{ fontFamily: 'var(--font-family-mono)' }}>{docId}</code>
            </div>
          ) : (
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', fontStyle: 'italic' }}>
              No document directly attached to this requirement.
            </div>
          )}
        </div>

        {/* OCR Text Trace & Inspection */}
        {ocrTrace && (
          <div style={{ border: '1px solid var(--color-border-subtle)', borderRadius: 'var(--radius-sm)', padding: 'var(--space-3)', backgroundColor: 'var(--color-bg-card)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
                  OCR Text Extraction
                </span>
                <span style={{ marginLeft: 'var(--space-2)' }}>
                  <Badge variant={ocrTrace.status === 'COMPLETED' ? 'success' : 'neutral'}>
                    {ocrTrace.status || 'PROCESSED'}
                  </Badge>
                </span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowOcrText(!showOcrText)}
              >
                {showOcrText ? 'Hide OCR Text' : 'View OCR Text'}
              </Button>
            </div>

            {showOcrText && (
              <div style={{ marginTop: 'var(--space-2)' }}>
                <pre
                  style={{
                    backgroundColor: 'var(--color-bg-subtle)',
                    padding: 'var(--space-3)',
                    borderRadius: 'var(--radius-xs)',
                    fontSize: '11px',
                    fontFamily: 'var(--font-family-mono)',
                    maxHeight: '180px',
                    overflowY: 'auto',
                    whiteSpace: 'pre-wrap',
                    color: 'var(--color-text-primary)',
                    border: '1px solid var(--color-border-subtle)',
                  }}
                >
                  {ocrTrace.text || 'No raw OCR text available.'}
                </pre>
              </div>
            )}
          </div>
        )}

        {/* AI Extracted Data Card */}
        {aiTrace && aiTrace.extraction && Object.keys(aiTrace.extraction).length > 0 && (
          <div style={{ border: '1px solid var(--color-border-subtle)', borderRadius: 'var(--radius-sm)', padding: 'var(--space-3)', backgroundColor: 'var(--color-bg-card)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
              <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
                Document AI Structured Data
              </div>
              <Badge variant="neutral">AI EXTRACTED</Badge>
            </div>
            <div style={{ backgroundColor: 'var(--color-bg-subtle)', padding: 'var(--space-3)', borderRadius: 'var(--radius-xs)', fontFamily: 'var(--font-family-mono)', fontSize: '11px', color: 'var(--color-text-secondary)', maxHeight: '160px', overflowY: 'auto' }}>
              <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                {JSON.stringify(aiTrace.extraction, null, 2)}
              </pre>
            </div>
          </div>
        )}

        {/* Government Registry Verification Card */}
        {govTrace && (
          <div style={{ border: '1px solid var(--color-border-subtle)', borderRadius: 'var(--radius-sm)', padding: 'var(--space-3)', backgroundColor: 'var(--color-bg-card)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
              <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
                Government Verification Record ({govTrace.source || 'OFFICIAL'})
              </div>
              <div style={{ display: 'flex', gap: 'var(--space-1)' }}>
                <Badge variant="neutral">DEMO PROVIDER</Badge>
                <Badge variant={govTrace.verification_result === 'MATCH' || govTrace.verification_result === 'VERIFIED' ? 'success' : 'warning'}>
                  {govTrace.verification_result || govTrace.status}
                </Badge>
              </div>
            </div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-2)' }}>
              <strong>Identifier:</strong> {govTrace.identifier || '—'} • <strong>Retrieved:</strong> {govTrace.retrieved_at ? new Date(govTrace.retrieved_at).toLocaleString() : '—'}
            </div>
            {govTrace.government_data && Object.keys(govTrace.government_data).length > 0 && (
              <div style={{ backgroundColor: 'var(--color-bg-subtle)', padding: 'var(--space-3)', borderRadius: 'var(--radius-xs)', fontFamily: 'var(--font-family-mono)', fontSize: '11px', color: 'var(--color-text-secondary)', maxHeight: '160px', overflowY: 'auto' }}>
                <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                  {JSON.stringify(govTrace.government_data, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}

        {/* Disclaimer Notice */}
        <div style={{ fontSize: '10px', color: 'var(--color-text-muted)', fontStyle: 'italic', padding: 'var(--space-2)', borderTop: '1px solid var(--color-border-subtle)' }}>
          Official Audit Record: All evidence items above were evaluated deterministically without LLM intervention. This report does not constitute an automated bidder qualification or disqualification decision.
        </div>
      </div>
    </Modal>
  );
}
