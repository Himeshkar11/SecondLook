import React from 'react';

const colors = { COMPLETED: '#15803d', PASS: '#15803d', FAILED: '#b91c1c', FAIL: '#b91c1c', PARTIAL: '#c2410c', NOT_VERIFIED: '#c2410c', PROCESSING: '#1d4ed8' };

export default function EvaluationStatusBadge({ status = 'INFORMATION' }) {
  return <span style={{ color: colors[status] || '#1d4ed8', fontWeight: 700, fontSize: 12 }}>{status.replaceAll('_', ' ')}</span>;
}
