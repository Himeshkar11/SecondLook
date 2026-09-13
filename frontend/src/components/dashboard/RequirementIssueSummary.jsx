import React from 'react';

export default function RequirementIssueSummary({ requirements = [] }) {
  return <section><h2>Requirement issues</h2><div style={{ overflowX: 'auto', background: '#fff', border: '1px solid #d9e2ec' }}><table style={{ width: '100%', borderCollapse: 'collapse' }}><thead><tr>{['Requirement', 'Total', 'Passed', 'Failed', 'Partial', 'Not verified'].map((label) => <th key={label} style={{ textAlign: 'left', padding: 12, fontSize: 12 }}>{label}</th>)}</tr></thead><tbody>{requirements.map((item) => <tr key={item.requirement_id}><td style={{ padding: 12 }}>{item.title}</td><td style={{ padding: 12 }}>{item.total}</td><td style={{ padding: 12 }}>{item.passed}</td><td style={{ padding: 12 }}>{item.failed}</td><td style={{ padding: 12 }}>{item.partial}</td><td style={{ padding: 12 }}>{item.not_verified}</td></tr>)}</tbody></table></div></section>;
}
