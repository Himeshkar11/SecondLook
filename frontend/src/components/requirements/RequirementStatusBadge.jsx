import React from 'react';
export default function RequirementStatusBadge({ status }) { return <strong>{String(status || 'UNKNOWN').replaceAll('_', ' ')}</strong>; }
