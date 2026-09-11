import React from 'react';
import { useNavigate } from 'react-router-dom';
import PageContainer from '../components/layout/PageContainer.jsx';
import StatCard from '../components/cards/StatCard.jsx';
import ComplianceCard from '../components/cards/ComplianceCard.jsx';
import RiskCard from '../components/cards/RiskCard.jsx';
import Badge from '../components/common/Badge.jsx';
import Button from '../components/common/Button.jsx';
import {
  DASHBOARD_STATS,
  COMPLIANCE_DATA,
  RISK_DATA,
  RECENT_TENDERS,
} from '../data/dashboardData.js';

/**
 * Complete Demo Dashboard (M19)
 * Clean, structured enterprise compliance portal dashboard
 */
export default function DashboardPage() {
  const navigate = useNavigate();
  const getStatusBadge = (status) => {
    switch (status) {
      case 'ACTIVE':
        return <Badge variant="success">Active</Badge>;
      case 'REVIEW':
        return <Badge variant="warning">Under Review</Badge>;
      case 'PENDING':
        return <Badge variant="info">Pending</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };

  const getRiskBadge = (risk) => {
    switch (risk) {
      case 'LOW':
        return <Badge variant="success">Low Risk</Badge>;
      case 'MEDIUM':
        return <Badge variant="warning">Med Risk</Badge>;
      case 'HIGH':
        return <Badge variant="danger">High Risk</Badge>;
      default:
        return <Badge variant="neutral">{risk}</Badge>;
    }
  };

  return (
    <PageContainer
      title="Compliance Dashboard"
      subtitle="GeM tender and bidder compliance oversight & statutory verification status"
      actions={
        <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
          <Button variant="secondary" size="sm" onClick={() => navigate('/audit')}>
            Audit Log
          </Button>
          <Button variant="primary" size="sm" onClick={() => navigate('/verification')}>
            + New Verification
          </Button>
        </div>
      }
    >
      {/* 1. Stat Cards Row */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: 'var(--space-4)',
          marginBottom: 'var(--space-6)',
        }}
      >
        {DASHBOARD_STATS.map((stat) => (
          <StatCard
            key={stat.id}
            title={stat.title}
            value={stat.value}
            context={stat.context}
            badgeText={stat.badgeText}
            badgeVariant={stat.badgeVariant}
            icon={stat.icon}
          />
        ))}
      </div>

      {/* 2. Main Content Layout: Tables (Left) + Overview Cards (Right) */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: 'var(--space-6)',
          alignItems: 'start',
        }}
        className="sl-dashboard-grid"
      >
        {/* Left Column: Recent Tenders Table */}
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
              <h3
                style={{
                  fontSize: 'var(--font-size-base)',
                  fontWeight: 'var(--font-weight-semibold)',
                  color: 'var(--color-text-primary)',
                }}
              >
                Recent Tenders Under Compliance
              </h3>
              <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                Active GeM procurement items with pending or verified submissions
              </p>
            </div>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
              Showing {RECENT_TENDERS.length} items
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
                  <th style={{ padding: 'var(--space-3) var(--space-5)' }}>Tender Reference</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Procuring Org</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'center' }}>Bids</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Status</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Risk Level</th>
                  <th style={{ padding: 'var(--space-3) var(--space-5)', textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {RECENT_TENDERS.map((tender, index) => (
                  <tr
                    key={tender.id}
                    style={{
                      borderBottom:
                        index === RECENT_TENDERS.length - 1 ? 'none' : '1px solid var(--color-border-subtle)',
                      transition: 'background-color var(--transition-fast)',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = 'var(--color-bg-hover)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }}
                  >
                    <td style={{ padding: 'var(--space-3) var(--space-5)' }}>
                      <div style={{ fontWeight: 'var(--font-weight-medium)', color: 'var(--color-primary)' }}>
                        {tender.id}
                      </div>
                      <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                        {tender.title}
                      </div>
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-xs)' }}>
                      {tender.organization}
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'center', fontWeight: 'var(--font-weight-semibold)' }}>
                      {tender.bids}
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                      {getStatusBadge(tender.status)}
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                      {getRiskBadge(tender.risk)}
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-5)', textAlign: 'right' }}>
                      <Button
                        variant="ghost"
                        size="sm"
                        style={{ color: 'var(--color-primary)' }}
                        onClick={() => navigate(`/tenders/${encodeURIComponent(tender.id)}`)}
                      >
                        View Details →
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column: Compliance & Risk Cards */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
          <ComplianceCard
            overallRate={COMPLIANCE_DATA.overallRate}
            breakdown={COMPLIANCE_DATA.breakdown}
          />
          <RiskCard
            riskLevel={RISK_DATA.riskLevel}
            score={RISK_DATA.score}
            factors={RISK_DATA.factors}
          />
        </div>
      </div>

      <style>{`
        @media (min-width: 1024px) {
          .sl-dashboard-grid {
            grid-template-columns: 2fr 1fr !important;
          }
        }
      `}</style>
    </PageContainer>
  );
}
