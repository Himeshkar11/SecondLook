import React from 'react';
import { Link } from 'react-router-dom';
import PageContainer from '../../components/layout/PageContainer.jsx';
import Badge from '../../components/common/Badge.jsx';
import Button from '../../components/common/Button.jsx';

const PLACEHOLDER_CONFIGS = {
  bids: {
    title: 'My Bids',
    subtitle: 'Submitted bids and procurement tender participation',
    milestone: 'Milestone 08',
    icon: '📝',
    emptyTitle: 'No submitted bids yet',
    emptyDescription: 'Bid submission will be available in the next stage of the bidder workspace (Milestone 08).',
    explanation:
      'In Milestone 08, suppliers will be able to prepare, attach statutory documents to, and submit bids for active procurement tenders.',
    actionLabel: 'Browse Published Tenders',
    actionPath: '/bidder/tenders',
  },
  documents: {
    title: 'Bidder Documents',
    subtitle: 'Statutory compliance document repository and verification records',
    milestone: 'Milestone 08',
    icon: '📁',
    emptyTitle: 'No documents uploaded yet',
    emptyDescription: 'Document upload and automated OCR processing will be available in the next stage (Milestone 08).',
    explanation:
      'In Milestone 08, bidders will be able to upload GST registration certificates, PAN cards, MSME Udyam documentation, and audited balance sheets for OCR extraction.',
    actionLabel: 'View Organization Profile',
    actionPath: '/bidder/profile',
  },
  compliance: {
    title: 'Statutory Compliance',
    subtitle: 'Automated compliance evaluations, scorecards, and evidence explainability',
    milestone: 'Milestone 09',
    icon: '🛡️',
    emptyTitle: 'No compliance evaluations yet',
    emptyDescription: 'Your compliance results will appear here after a bid evaluation is completed (Milestone 09).',
    explanation:
      'In Milestone 09, SecondLook will provide bidders with explainable compliance evaluations, rule-by-rule breakdowns, statutory evidence trace chains, and actionable remediation guidance.',
    actionLabel: 'Return to Workspace',
    actionPath: '/bidder',
  },
};

export default function BidderPlaceholderPage({ type = 'bids' }) {
  const config = PLACEHOLDER_CONFIGS[type] || PLACEHOLDER_CONFIGS.bids;

  return (
    <PageContainer
      title={config.title}
      subtitle={config.subtitle}
      actions={
        <Link to="/bidder" style={{ textDecoration: 'none' }}>
          <Button variant="outline" size="sm">
            ← Back to Workspace
          </Button>
        </Link>
      }
    >
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          textAlign: 'center',
          padding: 'var(--space-12) var(--space-6)',
          backgroundColor: 'var(--color-bg-card)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--color-border)',
          maxWidth: '700px',
          margin: 'var(--space-6) auto',
          gap: 'var(--space-4)',
        }}
      >
        <span style={{ fontSize: '48px', lineHeight: 1 }}>{config.icon}</span>

        <Badge variant="info">{config.milestone} Scope</Badge>

        <h2 style={{ fontSize: 'var(--font-size-xl)', fontWeight: 'var(--font-weight-bold)', margin: 0, color: 'var(--color-text-primary)' }}>
          {config.emptyTitle}
        </h2>

        <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', maxWidth: '480px', margin: 0, lineHeight: 1.5 }}>
          {config.emptyDescription}
        </p>

        <div
          style={{
            backgroundColor: 'var(--color-bg-subtle)',
            border: '1px solid var(--color-border-subtle)',
            borderRadius: 'var(--radius-sm)',
            padding: 'var(--space-3) var(--space-4)',
            fontSize: 'var(--font-size-xs)',
            color: 'var(--color-text-muted)',
            maxWidth: '520px',
            textAlign: 'left',
            lineHeight: 1.4,
          }}
        >
          <strong>Roadmap Note:</strong> {config.explanation}
        </div>

        <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-2)' }}>
          <Link to={config.actionPath} style={{ textDecoration: 'none' }}>
            <Button variant="primary">
              {config.actionLabel}
            </Button>
          </Link>
          <Link to="/bidder" style={{ textDecoration: 'none' }}>
            <Button variant="secondary">
              Dashboard
            </Button>
          </Link>
        </div>
      </div>
    </PageContainer>
  );
}
