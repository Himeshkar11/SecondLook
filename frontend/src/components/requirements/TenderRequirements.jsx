import React from 'react';
import RequirementCard from './RequirementCard.jsx';
export default function TenderRequirements({ requirements = [], onApprove, onReject, onEdit }) { return <section><h1>Tender requirements</h1><div style={{ display: 'grid', gap: 12 }}>{requirements.map((item) => <RequirementCard key={item.id} requirement={item} onApprove={onApprove} onReject={onReject} onEdit={onEdit} />)}</div></section>; }
