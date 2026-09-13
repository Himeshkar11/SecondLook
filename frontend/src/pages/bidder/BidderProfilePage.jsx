import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import PageContainer from '../../components/layout/PageContainer.jsx';
import Badge from '../../components/common/Badge.jsx';
import Button from '../../components/common/Button.jsx';
import Loading from '../../components/common/Loading.jsx';
import { getCurrentBidderProfile } from '../../services/bidderService.js';
import { maskIdentifier } from './BidderWorkspacePage.jsx';

export default function BidderProfilePage() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showMasked, setShowMasked] = useState(true);

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

  const statusUpper = (profile?.status || 'PENDING').toUpperCase();

  return (
    <PageContainer
      title="Bidder Organization Profile"
      subtitle="Verified business credentials, statutory registrations, and authorized contact information"
      actions={
        <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setShowMasked(!showMasked)}
          >
            {showMasked ? '👁️ Reveal Identifiers' : '🔒 Mask Identifiers'}
          </Button>
          <Link to="/bidder" style={{ textDecoration: 'none' }}>
            <Button variant="outline" size="sm">
              ← Back to Workspace
            </Button>
          </Link>
        </div>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)', maxWidth: '900px' }}>
        {loading ? (
          <div style={{ padding: 'var(--space-8)', textAlign: 'center' }}>
            <Loading message="Loading verified profile details..." size="lg" />
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
            {/* Statutory Integrity Notice */}
            <div
              style={{
                backgroundColor: 'var(--color-bg-subtle)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                padding: 'var(--space-4) var(--space-5)',
                display: 'flex',
                alignItems: 'flex-start',
                gap: 'var(--space-3)',
              }}
            >
              <span style={{ fontSize: '20px', lineHeight: 1 }}>🛡️</span>
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                <strong style={{ color: 'var(--color-text-primary)' }}>Read-Only Statutory Profile:</strong>
                <p style={{ margin: 'var(--space-1) 0 0 0' }}>
                  Statutory credentials (Legal Company Name, GSTIN, Income Tax PAN, and CIN) represent verified legal identity used during deterministic procurement compliance evaluations. Self-service modification of verified statutory attributes is restricted to preserve compliance audit integrity.
                </p>
              </div>
            </div>

            {/* Profile Overview Card */}
            <div
              style={{
                backgroundColor: 'var(--color-bg-card)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                padding: 'var(--space-6)',
                boxShadow: 'var(--shadow-xs)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  borderBottom: '1px solid var(--color-border)',
                  paddingBottom: 'var(--space-4)',
                  marginBottom: 'var(--space-5)',
                  flexWrap: 'wrap',
                  gap: 'var(--space-3)',
                }}
              >
                <div>
                  <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Entity Legal Name
                  </div>
                  <h2 style={{ fontSize: 'var(--font-size-xl)', fontWeight: 'var(--font-weight-bold)', margin: 'var(--space-1) 0 0 0', color: 'var(--color-text-primary)' }}>
                    {profile?.legal_name || '—'}
                  </h2>
                </div>
                <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                  <Badge variant="info">BIDDER Role</Badge>
                  <Badge variant={statusUpper === 'VERIFIED' ? 'success' : 'warning'}>
                    {statusUpper}
                  </Badge>
                </div>
              </div>

              {/* Grid of Profile Details */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                  gap: 'var(--space-5)',
                }}
              >
                <div>
                  <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Goods &amp; Services Tax (GSTIN)
                  </div>
                  <div style={{ fontSize: 'var(--font-size-base)', fontFamily: 'var(--font-family-mono)', marginTop: 'var(--space-1)', color: 'var(--color-text-primary)' }}>
                    {profile?.gst_number
                      ? (showMasked ? maskIdentifier(profile.gst_number, 'GST') : profile.gst_number)
                      : '—'}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Permanent Account Number (PAN)
                  </div>
                  <div style={{ fontSize: 'var(--font-size-base)', fontFamily: 'var(--font-family-mono)', marginTop: 'var(--space-1)', color: 'var(--color-text-primary)' }}>
                    {profile?.pan_number
                      ? (showMasked ? maskIdentifier(profile.pan_number, 'PAN') : profile.pan_number)
                      : '—'}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Registration Number / CIN
                  </div>
                  <div style={{ fontSize: 'var(--font-size-base)', fontFamily: 'var(--font-family-mono)', marginTop: 'var(--space-1)', color: 'var(--color-text-primary)' }}>
                    {profile?.registration_number || '—'}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Authorized Signatory
                  </div>
                  <div style={{ fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-medium)', marginTop: 'var(--space-1)', color: 'var(--color-text-primary)' }}>
                    {profile?.full_name || '—'}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Associated Email Address
                  </div>
                  <div style={{ fontSize: 'var(--font-size-base)', marginTop: 'var(--space-1)', color: 'var(--color-text-primary)' }}>
                    {profile?.email || '—'}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Profile Registration Date
                  </div>
                  <div style={{ fontSize: 'var(--font-size-base)', marginTop: 'var(--space-1)', color: 'var(--color-text-primary)' }}>
                    {profile?.created_at
                      ? new Date(profile.created_at).toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' })
                      : '—'}
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Actions / Links */}
            <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
              <Link to="/bidder/tenders" style={{ textDecoration: 'none' }}>
                <Button variant="primary">
                  📑 Browse Tenders
                </Button>
              </Link>
              <Link to="/bidder" style={{ textDecoration: 'none' }}>
                <Button variant="secondary">
                  📊 Return to Dashboard
                </Button>
              </Link>
            </div>
          </>
        )}
      </div>
    </PageContainer>
  );
}
