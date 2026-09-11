import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import PageContainer from '../components/layout/PageContainer.jsx';
import Badge from '../components/common/Badge.jsx';
import Button from '../components/common/Button.jsx';
import Loading from '../components/common/Loading.jsx';
import EmptyState from '../components/common/EmptyState.jsx';
import { getBidderById } from '../services/bidderService.js';

/**
 * BidderDetailPage — Dynamic Supabase-backed bidder profile.
 * Loads statutory details, associated tenders, and documents from FastAPI.
 */
export default function BidderDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const bidderId = decodeURIComponent(id || '');

  const [bidder, setBidder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notFound, setNotFound] = useState(false);

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

    try {
      const data = await getBidderById(bidderId);
      setBidder(data);
    } catch (err) {
      if (err?.status === 404 || err?.message?.includes('404')) {
        setNotFound(true);
      } else {
        setError('Unable to load bidder details. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  }, [bidderId]);

  useEffect(() => {
    fetchBidderDetails();
  }, [fetchBidderDetails]);

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
    </PageContainer>
  );
}
