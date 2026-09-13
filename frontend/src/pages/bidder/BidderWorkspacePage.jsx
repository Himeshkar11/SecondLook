import React from 'react';
import PageContainer from '../../components/layout/PageContainer.jsx';
import Badge from '../../components/common/Badge.jsx';
import { useAuth } from '../../auth/AuthContext.jsx';

/**
 * Minimal Bidder Workspace Shell (Milestone 05)
 * Verifies authenticated BIDDER routing and navigation.
 * Full bidder product features are scheduled for Milestones 07–09.
 */
export default function BidderWorkspacePage() {
  const { applicationUser } = useAuth();

  return (
    <PageContainer
      title="Bidder Workspace"
      subtitle="Statutory compliance & bid management portal"
    >
      <div style={{ display: 'grid', gap: 'var(--space-4)', maxWidth: '800px' }}>
        <div
          style={{
            backgroundColor: 'var(--color-bg-card)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-6)',
            boxShadow: 'var(--shadow-sm)',
            display: 'grid',
            gap: 'var(--space-3)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <h3 style={{ margin: 0, fontSize: 'var(--font-size-lg)', color: 'var(--color-text-primary)' }}>
              Welcome, {applicationUser?.full_name || 'Bidder'}
            </h3>
            <Badge variant="success">Active Bidder</Badge>
          </div>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)', margin: 0 }}>
            Your bidder account is active and authenticated.
          </p>
          <p style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-xs)', margin: 0 }}>
            Bid upload, compliance score tracking, failure explanations, and document verification workflows are scheduled for implementation in upcoming milestones (Milestones 07–09).
          </p>
        </div>
      </div>
    </PageContainer>
  );
}
