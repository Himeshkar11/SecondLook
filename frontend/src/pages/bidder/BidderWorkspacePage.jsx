import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import PageContainer from '../../components/layout/PageContainer.jsx';
import Badge from '../../components/common/Badge.jsx';
import Button from '../../components/common/Button.jsx';
import Loading from '../../components/common/Loading.jsx';
import { useAuth } from '../../auth/AuthContext.jsx';
import { getCurrentBidderProfile } from '../../services/bidderService.js';

export function maskIdentifier(val, type = 'GST') {
  if (!val || typeof val !== 'string') return '—';
  const trimmed = val.trim();
  if (type === 'GST' && trimmed.length >= 8) {
    return `${trimmed.slice(0, 2)}${'*'.repeat(Math.max(trimmed.length - 4, 6))}${trimmed.slice(-2)}`;
  }
  if (type === 'PAN' && trimmed.length >= 6) {
    return `${trimmed.slice(0, 2)}${'*'.repeat(Math.max(trimmed.length - 4, 5))}${trimmed.slice(-2)}`;
  }
  if (trimmed.length > 6) {
    return `${trimmed.slice(0, 2)}${'*'.repeat(trimmed.length - 4)}${trimmed.slice(-2)}`;
  }
  return trimmed;
}

export default function BidderWorkspacePage() {
  const { applicationUser } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    async function loadProfile() {
      setLoading(true);
      setError(null);
      try {
        const data = await getCurrentBidderProfile();
        if (isMounted) setProfile(data);
      } catch (err) {
        if (isMounted) {
          setError(err.message || 'Unable to load bidder profile.');
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadProfile();
    return () => { isMounted = false; };
  }, []);

  const companyName = profile?.legal_name || applicationUser?.full_name || 'Bidder';
  const statusUpper = (profile?.status || 'PENDING').toUpperCase();

  return (
    <PageContainer
      title={`Welcome, ${companyName}`}
      subtitle="SecondLook Bidder Workspace — Statutory compliance & procurement management"
      actions={
        <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
          <Link to="/bidder/profile" style={{ textDecoration: 'none' }}>
            <Button variant="secondary" size="sm">
              🏢 View Profile
            </Button>
          </Link>
          <Link to="/bidder/tenders" style={{ textDecoration: 'none' }}>
            <Button variant="primary" size="sm">
              📑 Browse Tenders
            </Button>
          </Link>
        </div>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
        {/* Milestone 07 Boundary & Transparency Banner */}
        <div
          style={{
            backgroundColor: 'var(--color-primary-subtle)',
            border: '1px solid var(--color-primary)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-4) var(--space-5)',
            display: 'flex',
            alignItems: 'flex-start',
            gap: 'var(--space-3)',
          }}
        >
          <span style={{ fontSize: '20px', lineHeight: 1 }}>🛡️</span>
          <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)' }}>
            <strong>Workspace Foundation Active (Milestone 07)</strong>
            <p style={{ margin: 'var(--space-1) 0 0 0', color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-xs)' }}>
              Your bidder identity and secure workspace are verified. Document upload and bid submissions open in <strong>Milestone 08</strong>; automated compliance evaluation and failure explanations will be active in <strong>Milestone 09</strong>.
            </p>
          </div>
        </div>

        {loading ? (
          <div style={{ padding: 'var(--space-8)', textAlign: 'center' }}>
            <Loading message="Loading bidder workspace details..." size="lg" />
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
        ) : (
          <>
            {/* Account Summary Card */}
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
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                  <h2 style={{ fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)', margin: 0 }}>
                    Verified Account Summary
                  </h2>
                  <Badge variant="info">Bidder Account</Badge>
                </div>
                <Badge variant={statusUpper === 'VERIFIED' ? 'success' : 'warning'}>
                  {statusUpper}
                </Badge>
              </div>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: 'var(--space-4)',
                }}
              >
                <div>
                  <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Company / Legal Name
                  </div>
                  <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 'var(--font-weight-medium)', marginTop: 'var(--space-1)', color: 'var(--color-text-primary)' }}>
                    {profile?.legal_name || '—'}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    GST Identification (GSTIN)
                  </div>
                  <div style={{ fontSize: 'var(--font-size-sm)', fontFamily: 'var(--font-family-mono)', marginTop: 'var(--space-1)', color: 'var(--color-text-primary)' }}>
                    {profile?.gst_number ? maskIdentifier(profile.gst_number, 'GST') : '—'}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Income Tax PAN
                  </div>
                  <div style={{ fontSize: 'var(--font-size-sm)', fontFamily: 'var(--font-family-mono)', marginTop: 'var(--space-1)', color: 'var(--color-text-primary)' }}>
                    {profile?.pan_number ? maskIdentifier(profile.pan_number, 'PAN') : '—'}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Registration / CIN
                  </div>
                  <div style={{ fontSize: 'var(--font-size-sm)', fontFamily: 'var(--font-family-mono)', marginTop: 'var(--space-1)', color: 'var(--color-text-primary)' }}>
                    {profile?.registration_number || '—'}
                  </div>
                </div>
              </div>
            </div>

            {/* Metric / Stat Overview Cards */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                gap: 'var(--space-4)',
              }}
            >
              {/* Active Tenders */}
              <div
                style={{
                  backgroundColor: 'var(--color-bg-card)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--space-4) var(--space-5)',
                  boxShadow: 'var(--shadow-xs)',
                }}
              >
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Associated Tenders
                </div>
                <div style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)', margin: 'var(--space-1) 0' }}>
                  {profile?.active_tenders_count ?? '0'}
                </div>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                  <Link to="/bidder/tenders" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>
                    Browse all available tenders →
                  </Link>
                </div>
              </div>

              {/* My Bids */}
              <div
                style={{
                  backgroundColor: 'var(--color-bg-card)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--space-4) var(--space-5)',
                  boxShadow: 'var(--shadow-xs)',
                }}
              >
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Submitted Bids
                </div>
                <div style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-muted)', margin: 'var(--space-1) 0' }}>
                  —
                </div>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                  Opens in Milestone 08
                </div>
              </div>

              {/* Compliance Score */}
              <div
                style={{
                  backgroundColor: 'var(--color-bg-card)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--space-4) var(--space-5)',
                  boxShadow: 'var(--shadow-xs)',
                }}
              >
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Compliance Score
                </div>
                <div style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-muted)', margin: 'var(--space-1) 0' }}>
                  —
                </div>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                  Evaluated in Milestone 09
                </div>
              </div>

              {/* Documents */}
              <div
                style={{
                  backgroundColor: 'var(--color-bg-card)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--space-4) var(--space-5)',
                  boxShadow: 'var(--shadow-xs)',
                }}
              >
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Uploaded Documents
                </div>
                <div style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)', margin: 'var(--space-1) 0' }}>
                  {profile?.documents_count ?? '0'}
                </div>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                  Upload workflow in Milestone 08
                </div>
              </div>
            </div>

            {/* Workspace Modules Navigation Grid */}
            <div>
              <h2 style={{ fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)', marginBottom: 'var(--space-3)' }}>
                Bidder Workspace Modules
              </h2>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                  gap: 'var(--space-4)',
                }}
              >
                {/* Tenders Module */}
                <Link
                  to="/bidder/tenders"
                  style={{
                    backgroundColor: 'var(--color-bg-card)',
                    border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-md)',
                    padding: 'var(--space-5)',
                    textDecoration: 'none',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 'var(--space-2)',
                    transition: 'border-color var(--transition-fast), transform var(--transition-fast)',
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--color-primary)'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--color-border)'; }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ fontSize: '24px' }}>📑</span>
                    <Badge variant="success">Available Now</Badge>
                  </div>
                  <h3 style={{ margin: 0, fontSize: 'var(--font-size-base)', color: 'var(--color-text-primary)' }}>
                    Published Tenders
                  </h3>
                  <p style={{ margin: 0, fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                    Browse live procurement tenders, review requirements, and monitor submission timelines.
                  </p>
                </Link>

                {/* My Bids Module */}
                <Link
                  to="/bidder/bids"
                  style={{
                    backgroundColor: 'var(--color-bg-card)',
                    border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-md)',
                    padding: 'var(--space-5)',
                    textDecoration: 'none',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 'var(--space-2)',
                    transition: 'border-color var(--transition-fast)',
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--color-primary)'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--color-border)'; }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ fontSize: '24px' }}>📝</span>
                    <Badge variant="neutral">Milestone 08</Badge>
                  </div>
                  <h3 style={{ margin: 0, fontSize: 'var(--font-size-base)', color: 'var(--color-text-primary)' }}>
                    My Bids
                  </h3>
                  <p style={{ margin: 0, fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                    Prepare, track, and manage your statutory bid submissions and tender participation.
                  </p>
                </Link>

                {/* Documents Module */}
                <Link
                  to="/bidder/documents"
                  style={{
                    backgroundColor: 'var(--color-bg-card)',
                    border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-md)',
                    padding: 'var(--space-5)',
                    textDecoration: 'none',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 'var(--space-2)',
                    transition: 'border-color var(--transition-fast)',
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--color-primary)'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--color-border)'; }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ fontSize: '24px' }}>📁</span>
                    <Badge variant="neutral">Milestone 08</Badge>
                  </div>
                  <h3 style={{ margin: 0, fontSize: 'var(--font-size-base)', color: 'var(--color-text-primary)' }}>
                    Document Repository
                  </h3>
                  <p style={{ margin: 0, fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                    Upload and manage GST, PAN, and corporate documentation with automated OCR extraction.
                  </p>
                </Link>

                {/* Compliance Module */}
                <Link
                  to="/bidder/compliance"
                  style={{
                    backgroundColor: 'var(--color-bg-card)',
                    border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-md)',
                    padding: 'var(--space-5)',
                    textDecoration: 'none',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 'var(--space-2)',
                    transition: 'border-color var(--transition-fast)',
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--color-primary)'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--color-border)'; }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ fontSize: '24px' }}>🛡️</span>
                    <Badge variant="neutral">Milestone 09</Badge>
                  </div>
                  <h3 style={{ margin: 0, fontSize: 'var(--font-size-base)', color: 'var(--color-text-primary)' }}>
                    Compliance &amp; Explainability
                  </h3>
                  <p style={{ margin: 0, fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                    Examine deterministic statutory compliance scores, evidence trace chains, and failure analyses.
                  </p>
                </Link>

                {/* Profile Module */}
                <Link
                  to="/bidder/profile"
                  style={{
                    backgroundColor: 'var(--color-bg-card)',
                    border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-md)',
                    padding: 'var(--space-5)',
                    textDecoration: 'none',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 'var(--space-2)',
                    transition: 'border-color var(--transition-fast)',
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--color-primary)'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--color-border)'; }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ fontSize: '24px' }}>🏢</span>
                    <Badge variant="success">Active</Badge>
                  </div>
                  <h3 style={{ margin: 0, fontSize: 'var(--font-size-base)', color: 'var(--color-text-primary)' }}>
                    Organization Profile
                  </h3>
                  <p style={{ margin: 0, fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                    View verified legal registration, statutory credentials, and authorized signatory details.
                  </p>
                </Link>
              </div>
            </div>
          </>
        )}
      </div>
    </PageContainer>
  );
}
