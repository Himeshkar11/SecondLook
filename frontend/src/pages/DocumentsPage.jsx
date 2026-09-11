import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import PageContainer from '../components/layout/PageContainer.jsx';
import Badge from '../components/common/Badge.jsx';
import Button from '../components/common/Button.jsx';
import Loading from '../components/common/Loading.jsx';
import EmptyState from '../components/common/EmptyState.jsx';
import { getAllDocuments, uploadDocument, getDocumentAccess } from '../services/documentService.js';
import { getBidders } from '../services/bidderService.js';

const DOCUMENT_TYPES = [
  { value: 'GST', label: 'GST Registration Certificate' },
  { value: 'PAN', label: 'Permanent Account Number (PAN)' },
  { value: 'UDYAM', label: 'Udyam MSME Registration' },
  { value: 'MCA', label: 'MCA Certificate of Incorporation' },
  { value: 'INCOME_TAX', label: 'Income Tax Return / Assessment' },
  { value: 'EPFO', label: 'EPFO Registration / Return' },
  { value: 'ESIC', label: 'ESIC Registration' },
  { value: 'STARTUP_INDIA', label: 'Startup India Certificate' },
  { value: 'NSIC', label: 'NSIC Registration' },
  { value: 'OEM_AUTHORIZATION', label: 'OEM Authorization Letter (MAF)' },
  { value: 'MAKE_IN_INDIA', label: 'Make in India Class-I/II Certificate' },
  { value: 'OTHER', label: 'Other Supporting Document' },
];

/**
 * DocumentsPage — Dynamic Supabase-backed document repository view.
 * Displays documents from the database and provides a secure upload interface.
 */
export default function DocumentsPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const initialBidderFilter = searchParams.get('bidder') || '';

  const [documents, setDocuments] = useState([]);
  const [bidders, setBidders] = useState([]);
  const [selectedBidderFilter, setSelectedBidderFilter] = useState(initialBidderFilter);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Upload Form State
  const [uploadBidderId, setUploadBidderId] = useState(initialBidderFilter);
  const [uploadDocType, setUploadDocType] = useState('GST');
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(null);
  const [uploadError, setUploadError] = useState(null);

  // Fetch initial bidders list and documents
  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [biddersRes, docsRes] = await Promise.all([
        getBidders(1, 100),
        getAllDocuments(selectedBidderFilter || null, 1, 100),
      ]);

      const bidderItems = biddersRes.items || [];
      setBidders(bidderItems);
      setDocuments(docsRes.items || []);

      if (!uploadBidderId && bidderItems.length > 0) {
        setUploadBidderId(bidderItems[0].id);
      }
    } catch (err) {
      setError('Unable to load documents repository. Please check connection and try again.');
    } finally {
      setLoading(false);
    }
  }, [selectedBidderFilter, uploadBidderId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Handle filter change
  const handleFilterChange = (e) => {
    const val = e.target.value;
    setSelectedBidderFilter(val);
    if (val) {
      setSearchParams({ bidder: val });
    } else {
      setSearchParams({});
    }
  };

  // Handle Document Upload
  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    setUploadError(null);
    setUploadSuccess(null);

    if (!uploadBidderId) {
      setUploadError('Please select a vendor / bidder.');
      return;
    }
    if (!uploadFile) {
      setUploadError('Please select a file to upload (.pdf, .png, .jpg, .jpeg).');
      return;
    }

    setUploading(true);
    try {
      const result = await uploadDocument(uploadBidderId, uploadFile, uploadDocType);
      setUploadSuccess(`Successfully uploaded "${result.file_name}" (${result.document_type}).`);
      setUploadFile(null);
      // Reset the file input DOM element if possible
      const fileInput = document.getElementById('document-file-input');
      if (fileInput) fileInput.value = '';

      // Reload document list
      const docsRes = await getAllDocuments(selectedBidderFilter || null, 1, 100);
      setDocuments(docsRes.items || []);
    } catch (err) {
      setUploadError(err.message || 'Failed to upload document. Please verify file type and size.');
    } finally {
      setUploading(false);
    }
  };

  // Handle View / Download Document via Signed URL
  const handleViewDocument = async (docId) => {
    try {
      const access = await getDocumentAccess(docId);
      if (access && access.download_url) {
        window.open(access.download_url, '_blank', 'noopener,noreferrer');
      } else {
        alert('Could not obtain document access link.');
      }
    } catch (err) {
      alert(`Unable to access document: ${err.message}`);
    }
  };

  const getDocStatusBadge = (status) => {
    switch (status) {
      case 'VERIFIED': return <Badge variant="success">Verified</Badge>;
      case 'UPLOADED': return <Badge variant="info">Uploaded</Badge>;
      case 'PENDING': return <Badge variant="warning">Pending</Badge>;
      case 'REJECTED': return <Badge variant="danger">Rejected</Badge>;
      default: return <Badge variant="neutral">{status}</Badge>;
    }
  };

  const statuses = ['VERIFIED', 'UPLOADED', 'PENDING', 'REJECTED'];

  return (
    <PageContainer
      title="Documents"
      subtitle="Uploaded tender documentation and compliance repository files"
      actions={<Badge variant="info">{documents.length} documents</Badge>}
    >
      {/* Upload Document Section */}
      <div
        style={{
          backgroundColor: 'var(--color-bg-card)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-5)',
          boxShadow: 'var(--shadow-xs)',
          marginBottom: 'var(--space-5)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-4)', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
          <div>
            <h2 style={{ fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-primary)' }}>
              Upload Compliance Document
            </h2>
            <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: '2px' }}>
              Files are securely stored in private storage with metadata tracked in PostgreSQL.
            </p>
          </div>
          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
            Max file size: 10 MB (PDF, PNG, JPG)
          </span>
        </div>

        {uploadSuccess && (
          <div
            style={{
              padding: 'var(--space-3) var(--space-4)',
              backgroundColor: 'rgba(16, 185, 129, 0.1)',
              border: '1px solid var(--color-success)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--color-success)',
              fontSize: 'var(--font-size-sm)',
              marginBottom: 'var(--space-4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span>✓ {uploadSuccess}</span>
            <button
              type="button"
              onClick={() => setUploadSuccess(null)}
              style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', fontWeight: 'bold' }}
            >
              ✕
            </button>
          </div>
        )}

        {uploadError && (
          <div
            style={{
              padding: 'var(--space-3) var(--space-4)',
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid var(--color-danger)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--color-danger)',
              fontSize: 'var(--font-size-sm)',
              marginBottom: 'var(--space-4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span>⚠ {uploadError}</span>
            <button
              type="button"
              onClick={() => setUploadError(null)}
              style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', fontWeight: 'bold' }}
            >
              ✕
            </button>
          </div>
        )}

        <form onSubmit={handleUploadSubmit} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 'var(--space-4)', alignItems: 'flex-end' }}>
          <div>
            <label style={{ display: 'block', fontSize: 'var(--font-size-xs)', fontWeight: 'var(--font-weight-medium)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-1)' }}>
              Vendor / Bidder *
            </label>
            <select
              value={uploadBidderId}
              onChange={(e) => setUploadBidderId(e.target.value)}
              style={{
                width: '100%',
                padding: 'var(--space-2) var(--space-3)',
                backgroundColor: 'var(--color-bg-input)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--color-text-primary)',
                fontSize: 'var(--font-size-sm)',
              }}
              required
            >
              {bidders.length === 0 && <option value="">Loading bidders...</option>}
              {bidders.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name || b.legal_name} ({b.pan || 'PAN'})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: 'var(--font-size-xs)', fontWeight: 'var(--font-weight-medium)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-1)' }}>
              Document Type *
            </label>
            <select
              value={uploadDocType}
              onChange={(e) => setUploadDocType(e.target.value)}
              style={{
                width: '100%',
                padding: 'var(--space-2) var(--space-3)',
                backgroundColor: 'var(--color-bg-input)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--color-text-primary)',
                fontSize: 'var(--font-size-sm)',
              }}
              required
            >
              {DOCUMENT_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.value} — {t.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: 'var(--font-size-xs)', fontWeight: 'var(--font-weight-medium)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-1)' }}>
              Select File * (.pdf, .png, .jpg)
            </label>
            <input
              id="document-file-input"
              type="file"
              accept=".pdf,.png,.jpg,.jpeg"
              onChange={(e) => setUploadFile(e.target.files[0] || null)}
              style={{
                width: '100%',
                padding: 'var(--space-1) var(--space-2)',
                backgroundColor: 'var(--color-bg-input)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--color-text-primary)',
                fontSize: 'var(--font-size-xs)',
              }}
              required
            />
          </div>

          <div>
            <Button
              type="submit"
              variant="primary"
              disabled={uploading}
              style={{ width: '100%' }}
            >
              {uploading ? 'Uploading to Storage...' : '↑ Upload Document'}
            </Button>
          </div>
        </form>
      </div>

      {/* Summary Status Badges */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          gap: 'var(--space-3)',
          marginBottom: 'var(--space-4)',
        }}
      >
        {statuses.map((status) => {
          const count = documents.filter((d) => d.status === status).length;
          const colors = {
            VERIFIED: 'var(--color-success)',
            UPLOADED: 'var(--color-primary)',
            PENDING: 'var(--color-warning)',
            REJECTED: 'var(--color-danger)',
          };
          return (
            <div
              key={status}
              style={{
                backgroundColor: 'var(--color-bg-card)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                padding: 'var(--space-4)',
                boxShadow: 'var(--shadow-xs)',
              }}
            >
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 'var(--space-1)' }}>
                {status.charAt(0) + status.slice(1).toLowerCase()}
              </div>
              <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 'var(--font-weight-bold)', color: colors[status] }}>
                {count}
              </div>
            </div>
          );
        })}
      </div>

      {/* Documents Table / Repository */}
      {loading ? (
        <Loading message="Loading documents repository..." />
      ) : error ? (
        <EmptyState
          title="Unable to load documents"
          description={error}
          actionLabel="Retry"
          onAction={loadData}
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
              <h2 style={{ fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-primary)' }}>
                Document Repository
              </h2>
              <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                Showing {documents.length} document record{documents.length === 1 ? '' : 's'}
              </span>
            </div>

            {/* Filter by Vendor */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <label style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                Filter Vendor:
              </label>
              <select
                value={selectedBidderFilter}
                onChange={handleFilterChange}
                style={{
                  padding: 'var(--space-1) var(--space-3)',
                  backgroundColor: 'var(--color-bg-input)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: 'var(--font-size-xs)',
                  color: 'var(--color-text-primary)',
                }}
              >
                <option value="">All Bidders</option>
                {bidders.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name || b.legal_name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {documents.length === 0 ? (
            <div style={{ padding: 'var(--space-8)' }}>
              <EmptyState
                title="No documents uploaded."
                description="There are currently no compliance documents uploaded for the selected criteria."
              />
            </div>
          ) : (
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
                    <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Vendor</th>
                    <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Filename</th>
                    <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Size</th>
                    <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Status</th>
                    <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Uploaded Date</th>
                    <th style={{ padding: 'var(--space-3) var(--space-5)', textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {documents.map((doc, index) => (
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
                        <Badge variant="neutral">{doc.document_type || doc.type}</Badge>
                      </td>
                      <td style={{ padding: 'var(--space-3) var(--space-4)', fontSize: 'var(--font-size-xs)' }}>
                        {doc.bidder_id || doc.bidderId ? (
                          <button
                            type="button"
                            style={{ background: 'none', border: 'none', color: 'var(--color-primary)', cursor: 'pointer', padding: 0, fontSize: 'var(--font-size-xs)', textAlign: 'left' }}
                            onClick={() => navigate(`/bidders/${doc.bidder_id || doc.bidderId}`)}
                          >
                            {doc.vendor_name || 'View Bidder'}
                          </button>
                        ) : (
                          doc.vendor_name || '—'
                        )}
                      </td>
                      <td style={{ padding: 'var(--space-3) var(--space-4)', fontFamily: 'var(--font-family-mono)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                        {doc.file_name || doc.filename}
                      </td>
                      <td style={{ padding: 'var(--space-3) var(--space-4)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                        {doc.size || '—'}
                      </td>
                      <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                        {getDocStatusBadge(doc.status)}
                      </td>
                      <td style={{ padding: 'var(--space-3) var(--space-4)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                        {doc.uploadedDate || (doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString('en-GB') : '—')}
                      </td>
                      <td style={{ padding: 'var(--space-3) var(--space-5)', textAlign: 'right' }}>
                        <Button
                          variant="ghost"
                          size="sm"
                          style={{ color: 'var(--color-primary)' }}
                          onClick={() => handleViewDocument(doc.id)}
                        >
                          👁 View / Download
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </PageContainer>
  );
}
