import React from 'react';
import PageContainer from '../components/layout/PageContainer.jsx';
import Badge from '../components/common/Badge.jsx';

/**
 * SettingsPage — M20
 * Platform configuration display — read-only demo settings.
 */

const THRESHOLD_SETTINGS = [
  { key: 'Minimum Compliance Score', value: '75%', description: 'Bidders below this threshold are flagged for review.', status: 'ACTIVE' },
  { key: 'Risk Auto-Escalation', value: '< 50%', description: 'Verifications scoring below this are automatically marked HIGH RISK.', status: 'ACTIVE' },
  { key: 'EPFO/ESIC Grace Period', value: '30 days', description: 'Maximum allowable delay for EPFO/ESIC filing before flagging.', status: 'ACTIVE' },
  { key: 'GST Return Tolerance', value: '2 quarters', description: 'Number of overdue GST returns before marking non-compliant.', status: 'ACTIVE' },
  { key: 'Blacklist Auto-Reject', value: 'Enabled', description: 'Automatically reject any bidder found in CVC blacklist registry.', status: 'ACTIVE' },
];

const API_REGISTRIES = [
  { name: 'Income Tax PAN Registry', status: 'DEMO', endpoint: '/api/v1/verification (demo provider)', type: 'IT Department' },
  { name: 'GSTN Portal', status: 'DEMO', endpoint: '/api/v1/verification (demo provider)', type: 'Ministry of Finance' },
  { name: 'Udyam Portal', status: 'DEMO', endpoint: '/api/v1/verification (demo provider)', type: 'MSME Ministry' },
  { name: 'MCA21', status: 'DEMO', endpoint: '/api/v1/verification (demo provider)', type: 'MCA' },
  { name: 'EPFO Portal', status: 'DEMO', endpoint: '/api/v1/verification (demo provider)', type: 'Ministry of Labour' },
  { name: 'CVC Blacklist Registry', status: 'DEMO', endpoint: '/api/v1/verification (demo provider)', type: 'CVC' },
  { name: 'DigiLocker', status: 'DEFERRED', endpoint: 'Not yet integrated', type: 'MeitY' },
];

export default function SettingsPage() {
  const cardStyle = {
    backgroundColor: 'var(--color-bg-card)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    boxShadow: 'var(--shadow-xs)',
    overflow: 'hidden',
  };

  const sectionHeader = (title, subtitle) => (
    <div style={{ padding: 'var(--space-4) var(--space-5)', borderBottom: '1px solid var(--color-border)' }}>
      <h2 style={{ fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-primary)' }}>
        {title}
      </h2>
      {subtitle && <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: '2px' }}>{subtitle}</p>}
    </div>
  );

  return (
    <PageContainer
      title="Settings"
      subtitle="Platform configuration, API registries, and compliance thresholds"
    >
      {/* Demo notice */}
      <div
        style={{
          backgroundColor: 'var(--color-bg-card)',
          border: '1px solid var(--color-border)',
          borderLeft: '4px solid var(--color-warning)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-4)',
          fontSize: 'var(--font-size-xs)',
          color: 'var(--color-text-secondary)',
        }}
      >
        <strong style={{ color: 'var(--color-text-primary)' }}>Demo Mode:</strong> All settings below are read-only reference values. Editing, user management, and API key configuration require authentication and administrator access, which are deferred to a future milestone.
      </div>

      {/* Compliance Thresholds */}
      <div style={cardStyle}>
        {sectionHeader('Compliance Thresholds', 'Score-based rules applied during vendor verification')}
        <div style={{ padding: 'var(--space-2)' }}>
          {THRESHOLD_SETTINGS.map((setting, index) => (
            <div
              key={setting.key}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                justifyContent: 'space-between',
                padding: 'var(--space-3) var(--space-4)',
                borderBottom: index === THRESHOLD_SETTINGS.length - 1 ? 'none' : '1px solid var(--color-border-subtle)',
                gap: 'var(--space-4)',
                flexWrap: 'wrap',
              }}
            >
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 'var(--font-weight-medium)', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)' }}>
                  {setting.key}
                </div>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: '2px' }}>
                  {setting.description}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', flexShrink: 0 }}>
                <span style={{ fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)', fontSize: 'var(--font-size-sm)', fontFamily: 'var(--font-family-mono)' }}>
                  {setting.value}
                </span>
                <Badge variant="success">{setting.status}</Badge>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* API Registry */}
      <div style={cardStyle}>
        {sectionHeader('Government API Registry', 'External registry integrations status')}
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
                <th style={{ padding: 'var(--space-3) var(--space-5)' }}>Registry</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Ministry / Department</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Integration Status</th>
                <th style={{ padding: 'var(--space-3) var(--space-5)' }}>Endpoint (Demo)</th>
              </tr>
            </thead>
            <tbody>
              {API_REGISTRIES.map((api, index) => (
                <tr
                  key={api.name}
                  style={{
                    borderBottom: index === API_REGISTRIES.length - 1 ? 'none' : '1px solid var(--color-border-subtle)',
                  }}
                >
                  <td style={{ padding: 'var(--space-3) var(--space-5)', fontWeight: 'var(--font-weight-medium)', color: 'var(--color-text-primary)' }}>
                    {api.name}
                  </td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                    {api.type}
                  </td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                    {api.status === 'DEMO' ? (
                      <Badge variant="warning">Demo Provider</Badge>
                    ) : api.status === 'DEFERRED' ? (
                      <Badge variant="neutral">Deferred</Badge>
                    ) : (
                      <Badge variant="success">Live</Badge>
                    )}
                  </td>
                  <td style={{ padding: 'var(--space-3) var(--space-5)', fontFamily: 'var(--font-family-mono)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                    {api.endpoint}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* System info */}
      <div style={{ ...cardStyle, padding: 'var(--space-5)' }}>
        <h2 style={{ fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-primary)', marginBottom: 'var(--space-4)' }}>
          System Information
        </h2>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: 'var(--space-4)',
          }}
        >
          {[
            { label: 'Application', value: 'SecondLook' },
            { label: 'Version', value: 'v0.1.0-demo' },
            { label: 'Milestone', value: 'M20 — Demo Portal' },
            { label: 'Backend', value: 'FastAPI / Python' },
            { label: 'Database', value: 'Supabase PostgreSQL' },
            { label: 'Frontend', value: 'React + Vite' },
            { label: 'Authentication', value: 'Deferred (Future Milestone)' },
            { label: 'RBAC', value: 'Deferred (Future Milestone)' },
          ].map((item) => (
            <div key={item.label}>
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '2px' }}>
                {item.label}
              </div>
              <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)', fontWeight: 'var(--font-weight-medium)' }}>
                {item.value}
              </div>
            </div>
          ))}
        </div>
      </div>
    </PageContainer>
  );
}
