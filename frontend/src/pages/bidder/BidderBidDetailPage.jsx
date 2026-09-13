import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import PageContainer from '../../components/layout/PageContainer.jsx';
import Badge from '../../components/common/Badge.jsx';
import Button from '../../components/common/Button.jsx';
import Loading from '../../components/common/Loading.jsx';
import Modal from '../../components/common/Modal.jsx';
import {
  getMyBidById,
  uploadBidDocument,
  submitBid,
  retryDocumentOcr,
  retryDocumentAi,
  verifyDocument,
  getDocumentAccess,
} from '../../services/bidService.js';

const ALLOWED_TYPES = [
  { value: 'GST', label: 'GST Certificate (Statutory)' },
  { value: 'PAN', label: 'PAN Card (Statutory)' },
  { value: 'UDYAM', label: 'Udyam / MSME Certificate (Statutory)' },
  { value: 'TECHNICAL_DOCUMENT', label: 'Technical Proposal / Specification' },
  { value: 'FINANCIAL_DOCUMENT', label: 'Financial Declaration / Audit Statement' },
  { value: 'SUPPORTING_DOCUMENT', label: 'Supporting Corporate Certificate' },
  { value: 'OTHER', label: 'Other Document' },
];

export default function BidderBidDetailPage() {
  const { bidId } = useParams();
  const [bid, setBid] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionError, setActionError] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);

  // Upload State
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedType, setSelectedType] = useState('TECHNICAL_DOCUMENT');
  const [uploading, setUploading] = useState(false);

  // Processing Action State (per doc ID)
  const [retryingDocId, setRetryingDocId] = useState(null);

  // Submit Modal State
  const [showSubmitModal, setShowSubmitModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const fetchBid = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getMyBidById(bidId);
      setBid(data);
    } catch (err) {
      setError(err.message || 'Unable to load bid workspace.');
    } finally {
      setLoading(false);
    }
  }, [bidId]);

  useEffect(() => {
    fetchBid();
  }, [fetchBid]);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setActionError(null);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setActionError('Please select a file to upload (.pdf, .png, .jpg).');
      return;
    }
    setUploading(true);
    setActionError(null);
    setActionSuccess(null);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('document_type', selectedType);

    try {
      await uploadBidDocument(bidId, formData);
      setSelectedFile(null);
      // Reset file input element
      const fileInput = document.getElementById('bid-file-input');
      if (fileInput) fileInput.value = '';
      setActionSuccess('Document uploaded successfully. OCR and AI extraction pipeline queued.');
      // Refresh bid details
      await fetchBid();
    } catch (err) {
      setActionError(err.message || 'Failed to upload document.');
    } finally {
      setUploading(false);
    }
  };

  const handleDownloadAccess = async (docId, fileName) => {
    try {
      const res = await getDocumentAccess(docId);
      if (res?.url) {
        window.open(res.url, '_blank', 'noopener,noreferrer');
      } else {
        setActionError('Unable to generate temporary secure access URL.');
      }
    } catch (err) {
      setActionError(err.message || 'Failed to access document.');
    }
  };

  const handleRetryOcr = async (docId) => {
    setRetryingDocId(docId);
    setActionError(null);
    try {
      await retryDocumentOcr(docId);
      setActionSuccess('OCR processing re-queued for document.');
      await fetchBid();
    } catch (err) {
      setActionError(err.message || 'Failed to retry OCR.');
    } finally {
      setRetryingDocId(null);
    }
  };

  const handleRetryAi = async (docId) => {
    setRetryingDocId(docId);
    setActionError(null);
    try {
      await retryDocumentAi(docId);
      setActionSuccess('AI extraction re-queued for document.');
      await fetchBid();
    } catch (err) {
      setActionError(err.message || 'Failed to retry AI extraction.');
    } finally {
      setRetryingDocId(null);
    }
  };

  const handleVerify = async (docId) => {
    setRetryingDocId(docId);
    setActionError(null);
    try {
      await verifyDocument(docId);
      setActionSuccess('Statutory government verification executed.');
      await fetchBid();
    } catch (err) {
      setActionError(err.message || 'Government verification failed or prerequisite not met.');
    } finally {
      setRetryingDocId(null);
    }
  };

  const handleConfirmSubmit = async () => {
    setSubmitting(true);
    setActionError(null);
    try {
      await submitBid(bidId);
      setShowSubmitModal(false);
      setActionSuccess('Bid submitted successfully for statutory officer evaluation.');
      await fetchBid();
    } catch (err) {
      setActionError(err.message || 'Failed to submit bid.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <PageContainer title="Tender Bid Workspace" subtitle="Loading bid workspace details...">
        <div style={{ padding: 'var(--space-8)', textAlign: 'center' }}>
          <Loading message="Loading bid workspace..." size="lg" />
        </div>
      </PageContainer>
    );
  }

  if (error || !bid) {
    return (
      <PageContainer title="Tender Bid Workspace" subtitle="Error loading workspace">
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
          ⚠️ {error || 'Bid not found or access denied.'}
        </div>
        <div style={{ marginTop: 'var(--space-4)' }}>
          <Link to="/bidder/bids" style={{ textDecoration: 'none' }}>
            <Button variant="outline">← Back to My Bids</Button>
          </Link>
        </div>
      </PageContainer>
    );
  }

  const isSubmitted = (bid.status || '').toUpperCase() === 'SUBMITTED';

  const getStatusBadge = (status) => {
    if (status === 'SUBMITTED') {
      return <Badge variant="success">Submitted</Badge>;
    }
    return <Badge variant="warning">Draft Workspace</Badge>;
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '—';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <PageContainer
      title={`Bid Workspace: ${bid.tender_title || 'Tender Submission'}`}
      subtitle={`Reference: ${bid.tender_reference_number || 'N/A'} | Status: ${bid.status}`}
      actions={
        <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
          <Link to={`/bidder/bids/${bid.id}/compliance`} style={{ textDecoration: 'none' }}>
            <Button variant="secondary" size="sm">
              Compliance Score →
            </Button>
          </Link>
          <Link to="/bidder/bids" style={{ textDecoration: 'none' }}>
            <Button variant="outline" size="sm">
              ← All Bids
            </Button>
          </Link>
          <Link to="/bidder/tenders" style={{ textDecoration: 'none' }}>
            <Button variant="outline" size="sm">
              Browse Tenders
            </Button>
          </Link>
        </div>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
        {/* Important Legal Boundary Notice */}
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
          <strong>Statutory Submission Boundary:</strong> Submitting this bid workspace registers your proposal for official procurement officer evaluation. Submission strictly <em>does not</em> constitute qualification, approval, or contract award. Bids remain immutable once submitted.
        </div>

        {/* Feedback Messages */}
        {actionError && (
          <div
            style={{
              backgroundColor: 'var(--color-danger-subtle, #fee2e2)',
              border: '1px solid var(--color-danger, #ef4444)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-3) var(--space-4)',
              color: 'var(--color-danger, #ef4444)',
              fontSize: 'var(--font-size-xs)',
            }}
          >
            ⚠️ {actionError}
          </div>
        )}
        {actionSuccess && (
          <div
            style={{
              backgroundColor: 'var(--color-success-subtle, #f0fdf4)',
              border: '1px solid var(--color-success, #22c55e)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-3) var(--space-4)',
              color: 'var(--color-success, #22c55e)',
              fontSize: 'var(--font-size-xs)',
            }}
          >
            ✓ {actionSuccess}
          </div>
        )}

        {/* Workspace Summary Card */}
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
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: '1px solid var(--color-border)',
              paddingBottom: 'var(--space-3)',
              marginBottom: 'var(--space-4)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
              <h2 style={{ fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)', margin: 0 }}>
                Tender Submission Metadata
              </h2>
              {getStatusBadge(bid.status)}
            </div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
              Workspace ID: <code style={{ fontFamily: 'var(--font-mono)' }}>{bid.id}</code>
            </div>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: 'var(--space-4)',
            }}
          >
            <div>
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
                Tender Title
              </div>
              <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 'var(--font-weight-medium)', marginTop: 'var(--space-1)' }}>
                {bid.tender_title || 'N/A'}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
                Reference Number
              </div>
              <div style={{ fontSize: 'var(--font-size-sm)', fontFamily: 'var(--font-mono)', marginTop: 'var(--space-1)' }}>
                {bid.tender_reference_number || 'N/A'}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
                Attached Documents
              </div>
              <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 'var(--font-weight-medium)', marginTop: 'var(--space-1)' }}>
                {bid.documents?.length || 0} document(s)
              </div>
            </div>
            <div>
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
                Created At
              </div>
              <div style={{ fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
                {new Date(bid.created_at).toLocaleString()}
              </div>
            </div>
            {isSubmitted && (
              <div>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
                  Submitted At
                </div>
                <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-success, #22c55e)', fontWeight: 'var(--font-weight-semibold)', marginTop: 'var(--space-1)' }}>
                  {bid.submitted_at ? new Date(bid.submitted_at).toLocaleString() : 'Submitted'}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Document Upload Section (Draft Mode Only) */}
        {!isSubmitted ? (
          <div
            style={{
              backgroundColor: 'var(--color-bg-card)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-5)',
              boxShadow: 'var(--shadow-xs)',
            }}
          >
            <h3 style={{ margin: '0 0 var(--space-3) 0', fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)' }}>
              Upload Proposal &amp; Statutory Documents
            </h3>
            <p style={{ margin: '0 0 var(--space-4) 0', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
              Upload required statutory certificates (GST, PAN, MSME) or technical proposals. Uploaded files are automatically queued for OCR text extraction and structured AI extraction.
            </p>

            <form onSubmit={handleUpload} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap', alignItems: 'flex-end' }}>
                <div style={{ flex: '1 1 240px' }}>
                  <label
                    htmlFor="bid-doc-type"
                    style={{ display: 'block', fontSize: 'var(--font-size-xs)', fontWeight: 'var(--font-weight-medium)', marginBottom: 'var(--space-1)' }}
                  >
                    Document Type
                  </label>
                  <select
                    id="bid-doc-type"
                    value={selectedType}
                    onChange={(e) => setSelectedType(e.target.value)}
                    style={{
                      width: '100%',
                      padding: 'var(--space-2) var(--space-3)',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--color-border)',
                      backgroundColor: 'var(--color-bg-subtle)',
                      fontSize: 'var(--font-size-sm)',
                      color: 'var(--color-text-primary)',
                    }}
                  >
                    {ALLOWED_TYPES.map((t) => (
                      <option key={t.value} value={t.value}>
                        {t.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div style={{ flex: '2 1 300px' }}>
                  <label
                    htmlFor="bid-file-input"
                    style={{ display: 'block', fontSize: 'var(--font-size-xs)', fontWeight: 'var(--font-weight-medium)', marginBottom: 'var(--space-1)' }}
                  >
                    Select File (.pdf, .png, .jpg, .jpeg)
                  </label>
                  <input
                    id="bid-file-input"
                    type="file"
                    accept=".pdf,.png,.jpg,.jpeg"
                    onChange={handleFileChange}
                    style={{
                      width: '100%',
                      padding: 'var(--space-2)',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--color-border)',
                      backgroundColor: 'var(--color-bg-subtle)',
                      fontSize: 'var(--font-size-sm)',
                      color: 'var(--color-text-primary)',
                    }}
                  />
                </div>

                <div>
                  <Button
                    type="submit"
                    variant="primary"
                    disabled={uploading || !selectedFile}
                  >
                    {uploading ? 'Uploading & Enqueuing...' : 'Upload Document'}
                  </Button>
                </div>
              </div>
            </form>
          </div>
        ) : (
          <div
            style={{
              backgroundColor: 'var(--color-bg-muted)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-4) var(--space-5)',
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-3)',
              fontSize: 'var(--font-size-sm)',
              color: 'var(--color-text-secondary)',
            }}
          >
            <span>🔒</span>
            <span>
              <strong>Workspace Locked:</strong> This tender bid proposal has been submitted. No additional documents can be added or modified.
            </span>
          </div>
        )}

        {/* Documents Table & Processing Status */}
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
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: '1px solid var(--color-border)',
              paddingBottom: 'var(--space-3)',
              marginBottom: 'var(--space-4)',
            }}
          >
            <h3 style={{ margin: 0, fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)' }}>
              Attached Proposal Documents &amp; Processing Pipeline
            </h3>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
              {bid.documents?.length || 0} document(s)
            </span>
          </div>

          {!bid.documents || bid.documents.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 'var(--space-6)', color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>
              No documents attached to this bid workspace yet. Upload required statutory certificates to enable submission.
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--font-size-sm)' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--color-border)', textAlign: 'left' }}>
                    <th style={{ padding: 'var(--space-2) var(--space-3)', color: 'var(--color-text-muted)', fontWeight: 'var(--font-weight-medium)' }}>File Name</th>
                    <th style={{ padding: 'var(--space-2) var(--space-3)', color: 'var(--color-text-muted)', fontWeight: 'var(--font-weight-medium)' }}>Type</th>
                    <th style={{ padding: 'var(--space-2) var(--space-3)', color: 'var(--color-text-muted)', fontWeight: 'var(--font-weight-medium)' }}>Size</th>
                    <th style={{ padding: 'var(--space-2) var(--space-3)', color: 'var(--color-text-muted)', fontWeight: 'var(--font-weight-medium)' }}>OCR Pipeline</th>
                    <th style={{ padding: 'var(--space-2) var(--space-3)', color: 'var(--color-text-muted)', fontWeight: 'var(--font-weight-medium)' }}>AI Extraction</th>
                    <th style={{ padding: 'var(--space-2) var(--space-3)', color: 'var(--color-text-muted)', fontWeight: 'var(--font-weight-medium)' }}>Verification</th>
                    <th style={{ padding: 'var(--space-2) var(--space-3)', color: 'var(--color-text-muted)', fontWeight: 'var(--font-weight-medium)', textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {bid.documents.map((doc) => {
                    const ocrDone = doc.ocr_status === 'OCR_COMPLETED';
                    const ocrFailed = doc.ocr_status === 'OCR_FAILED';
                    const aiDone = doc.ai_status === 'AI_COMPLETED';
                    const aiFailed = doc.ai_status === 'AI_FAILED';
                    const isRetrying = retryingDocId === doc.id;
                    const canVerify = ['GST', 'PAN'].includes((doc.document_type || '').toUpperCase());

                    return (
                      <tr key={doc.id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                        <td style={{ padding: 'var(--space-3)', fontWeight: 'var(--font-weight-medium)' }}>
                          {doc.file_name}
                        </td>
                        <td style={{ padding: 'var(--space-3)' }}>
                          <Badge variant="info">{doc.document_type}</Badge>
                        </td>
                        <td style={{ padding: 'var(--space-3)', color: 'var(--color-text-secondary)' }}>
                          {formatFileSize(doc.file_size)}
                        </td>
                        <td style={{ padding: 'var(--space-3)' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                            {ocrDone ? (
                              <Badge variant="success">OCR Done</Badge>
                            ) : ocrFailed ? (
                              <>
                                <Badge variant="danger">OCR Failed</Badge>
                                {!isSubmitted && (
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    disabled={isRetrying}
                                    onClick={() => handleRetryOcr(doc.id)}
                                  >
                                    Retry
                                  </Button>
                                )}
                              </>
                            ) : (
                              <Badge variant="neutral">{doc.ocr_status || 'QUEUED'}</Badge>
                            )}
                          </div>
                        </td>
                        <td style={{ padding: 'var(--space-3)' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                            {aiDone ? (
                              <Badge variant="success">Extracted</Badge>
                            ) : aiFailed ? (
                              <>
                                <Badge variant="danger">AI Failed</Badge>
                                {!isSubmitted && ocrDone && (
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    disabled={isRetrying}
                                    onClick={() => handleRetryAi(doc.id)}
                                  >
                                    Retry
                                  </Button>
                                )}
                              </>
                            ) : (
                              <Badge variant="neutral">{doc.ai_status || 'PENDING'}</Badge>
                            )}
                          </div>
                        </td>
                        <td style={{ padding: 'var(--space-3)' }}>
                          {canVerify ? (
                            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                              <Badge variant={doc.verification_status === 'COMPLETED' ? 'success' : 'neutral'}>
                                {doc.verification_status || 'PENDING'}
                              </Badge>
                              {!isSubmitted && aiDone && doc.verification_status !== 'COMPLETED' && (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  disabled={isRetrying}
                                  onClick={() => handleVerify(doc.id)}
                                >
                                  Verify
                                </Button>
                              )}
                            </div>
                          ) : (
                            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>—</span>
                          )}
                        </td>
                        <td style={{ padding: 'var(--space-3)', textAlign: 'right' }}>
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => handleDownloadAccess(doc.id, doc.file_name)}
                          >
                            Secure Access
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Submission Action Bar */}
        <div
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
          }}
        >
          <div>
            <h4 style={{ margin: '0 0 var(--space-1) 0', fontSize: 'var(--font-size-sm)', fontWeight: 'var(--font-weight-semibold)' }}>
              {isSubmitted ? 'Proposal Submission Status' : 'Ready to Submit Proposal?'}
            </h4>
            <p style={{ margin: 0, fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
              {isSubmitted
                ? 'Your proposal is locked and awaiting officer statutory review.'
                : 'Submitting requires at least one attached document. Submission will lock further file uploads.'}
            </p>
          </div>

          <div>
            {!isSubmitted ? (
              <Button
                variant="primary"
                disabled={!bid.documents || bid.documents.length === 0}
                onClick={() => setShowSubmitModal(true)}
              >
                Submit Formal Bid Proposal →
              </Button>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
                <Badge variant="success" size="lg">
                  ✓ Proposal Formally Submitted
                </Badge>
                <Link to={`/bidder/bids/${bid.id}/compliance`} style={{ textDecoration: 'none' }}>
                  <Button variant="primary">
                    View Compliance Score &amp; Assessment →
                  </Button>
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Submission Confirmation Modal */}
        {showSubmitModal && (
          <Modal
            isOpen={showSubmitModal}
            title="Confirm Formal Bid Submission"
            onClose={() => setShowSubmitModal(false)}
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              <p style={{ margin: 0, fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
                Are you ready to submit your formal proposal for <strong>{bid.tender_title}</strong>?
              </p>

              <div
                style={{
                  backgroundColor: 'var(--color-warning-subtle, #fefce8)',
                  border: '1px solid var(--color-warning, #eab308)',
                  borderRadius: 'var(--radius-sm)',
                  padding: 'var(--space-3) var(--space-4)',
                  fontSize: 'var(--font-size-xs)',
                  color: 'var(--color-text-primary)',
                  lineHeight: 1.4,
                }}
              >
                <strong>Notice of Irreversibility:</strong>
                <ul style={{ margin: 'var(--space-1) 0 0 var(--space-4)', padding: 0 }}>
                  <li>Once submitted, this bid workspace is permanently locked.</li>
                  <li>Attached documents cannot be replaced or deleted.</li>
                  <li>Submission enters your bid into the officer compliance evaluation queue.</li>
                  <li><strong>Submission does not guarantee qualification, approval, or contract award.</strong></li>
                </ul>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--space-2)', marginTop: 'var(--space-2)' }}>
                <Button
                  variant="secondary"
                  disabled={submitting}
                  onClick={() => setShowSubmitModal(false)}
                >
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  disabled={submitting}
                  onClick={handleConfirmSubmit}
                >
                  {submitting ? 'Submitting Proposal...' : 'Yes, Submit My Bid'}
                </Button>
              </div>
            </div>
          </Modal>
        )}
      </div>
    </PageContainer>
  );
}
