import React from 'react';

export default function EvaluationStats({ summary = {} }) {
  const items = [['Bidders', summary.total_bidders], ['Evaluated', summary.evaluated], ['Completed', summary.completed], ['Processing', summary.processing], ['Attention', summary.attention_required], ['Reviews pending', summary.reviews_pending]];
  return <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(130px,1fr))', gap: 12 }}>{items.map(([label, value]) => <div key={label} style={{ border: '1px solid #d9e2ec', padding: 16, background: '#fff' }}><div style={{ color: '#52606d', fontSize: 12 }}>{label}</div><strong style={{ fontSize: 24 }}>{value ?? 0}</strong></div>)}</div>;
}
