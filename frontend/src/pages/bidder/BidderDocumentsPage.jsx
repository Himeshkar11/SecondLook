import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import PageContainer from '../../components/layout/PageContainer.jsx';
import Badge from '../../components/common/Badge.jsx';
import Button from '../../components/common/Button.jsx';
import Loading from '../../components/common/Loading.jsx';
import EmptyState from '../../components/common/EmptyState.jsx';
import { getMyBids, getDocumentAccess } from '../../services/bidService.js';

export default function BidderDocumentsPage() {
  const [bids, setBids] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getMyBids();
      setBids(data || []);
    } catch (err) {
      setError(err.message || 'Unable to load documents.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  // Aggregate all documents from all bids
  const allDocuments = bids.flatMap((b) =>
    (b.documents || []).map((d) => ({
      ...d,
      bidId: b.id,
      tenderTitle: b.tender_title,
      tenderRef: b.tender_reference_number,
      bidStatus: b.status,
    }))
  );

  const handleDownloadAccess = async (docId) => {
    try {
      const res = await getDocumentAccess(docId);
      if (res?.url) {
        window.open(res.url, '_blank', 'noopener,noreferrer');
      } else {
        alert('Unable to generate secure download URL.');
      }
    } catch (err) {
      alert(err.message || 'Failed to generate signed document access.');
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '—';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <PageContainer
      title="Bidder Document Repository"
      subtitle="Statutory compliance certificates and proposal documents attached across your tender submissions"
      actions={
        <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
          <Link to="/bidder" style={{ textDecoration: 'none' }}>
            <Button variant="outline" size="sm">
              ← Workspace
            </Button>
          </Link>
          <Link to="/bidder/bids" style={{ textDecoration: 'none' }}>
            <Button variant="primary" size="sm">
              My Bids
            </Button>
          </Link>
        </div>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
        {/* Notice Card */}
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
            <span style={{ fontSize: 'var(--font-size-sm)', fontWeight: 'var(--font-weight-semibold)' }}>
              Secure Encrypted Storage
            </span>
            <p style={{ margin: 'var(--space-1) 0 0 0', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
              All documents are stored in private, access-controlled cloud storage. Temporary signed URLs expire automatically after use.
            </p>
          </div>
          <div style={{ padding: 'var(--space-2) var(--space-4)', backgroundColor: 'var(--color-bg-muted)', borderRadius: 'var(--radius-sm)', textAlign: 'center' }}>
            <div style={{ fontSize: 'var(--font-size-lg)', fontWeight: 'var(--font-weight-bold)' }}>{allDocuments.length}</div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>Uploaded Documents</div>
          </div>
        </div>

        {/* Content Area */}
        {loading ? (
          <div style={{ padding: 'var(--space-8)', textAlign: 'center' }}>
            <Loading message="Loading document repository..." size="lg" />
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
        ) : allDocuments.length === 0 ? (
          <div
            style={{
              backgroundColor: 'var(--color-bg-card)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-8)',
            }}
          >
            <EmptyState
              title="No documents uploaded"
              description="No documents have been attached to any of your bids yet. Start or open a tender bid workspace to upload certificates."
              action={
                <Link to="/bidder/bids" style={{ textDecoration: 'none' }}>
                  <Button variant="primary">View My Bids</Button>
                </Link>
              }
            />
          </div>
        ) : (
          <div
            style={{
              backgroundColor: 'var(--color-bg-card)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-5)',
              boxShadow: 'var(--shadow-xs)',
              overflowX: 'auto',
            }}
          >
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--font-size-sm)' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--color-border)', textAlign: 'left' }}>
                  <th style={{ padding: 'var(--space-2) var(--space-3)', color: 'var(--color-text-muted)', fontWeight: 'var(--font-weight-medium)' }}>File Name</th>
                  <th style={{ padding: 'var(--space-2) var(--space-3)', color: 'var(--color-text-muted)', fontWeight: 'var(--font-weight-medium)' }}>Type</th>
                  <th style={{ padding: 'var(--space-2) var(--space-3)', color: 'var(--color-text-muted)', fontWeight: 'var(--font-weight-medium)' }}>Tender / Bid Workspace</th>
                  <th style={{ padding: 'var(--space-2) var(--space-3)', color: 'var(--color-text-muted)', fontWeight: 'var(--font-weight-medium)' }}>Size</th>
                  <th style={{ padding: 'var(--space-2) var(--space-3)', color: 'var(--color-text-muted)', fontWeight: 'var(--font-weight-medium)' }}>OCR Pipeline</th>
                  <th style={{ padding: 'var(--space-2) var(--space-3)', color: 'var(--color-text-muted)', fontWeight: 'var(--font-weight-medium)' }}>AI Extraction</th>
                  <th style={{ padding: 'var(--space-2) var(--space-3)', color: 'var(--color-text-muted)', fontWeight: 'var(--font-weight-medium)', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {allDocuments.map((doc) => (
                  <tr key={doc.id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                    <td style={{ padding: 'var(--space-3)', fontWeight: 'var(--font-weight-medium)' }}>
                      {doc.file_name}
                    </td>
                    <td style={{ padding: 'var(--space-3)' }}>
                      <Badge variant="info">{doc.document_type}</Badge>
                    </td>
                    <td style={{ padding: 'var(--space-3)' }}>
                      <Link
                        to={`/bidder/bids/${doc.bidId}`}
                        style={{ color: 'var(--color-primary)', textDecoration: 'none', fontWeight: 'var(--font-weight-medium)' }}
                      >
                        {doc.tenderTitle || 'View Workspace'}
                      </Link>
                    </td>
                    <td style={{ padding: 'var(--space-3)', color: 'var(--color-text-secondary)' }}>
                      {formatFileSize(doc.file_size)}
                    </td>
                    <td style={{ padding: 'var(--space-3)' }}>
                      <Badge variant={doc.ocr_status === 'OCR_COMPLETED' ? 'success' : doc.ocr_status === 'OCR_FAILED' ? 'danger' : 'neutral'}>
                        {doc.ocr_status || 'QUEUED'}
                      </Badge>
                    </td>
                    <td style={{ padding: 'var(--space-3)' }}>
                      <Badge variant={doc.ai_status === 'AI_COMPLETED' ? 'success' : doc.ai_status === 'AI_FAILED' ? 'danger' : 'neutral'}>
                        {doc.ai_status || 'PENDING'}
                      </Badge>
                    </td>
                    <td style={{ padding: 'var(--space-3)', textAlign: 'right' }}>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => handleDownloadAccess(doc.id)}
                      >
                        Secure Access
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </PageContainer>
  );
}
