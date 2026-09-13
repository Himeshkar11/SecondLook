import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import PageContainer from '../components/layout/PageContainer.jsx';
import TenderEvaluationDashboard from '../components/dashboard/TenderEvaluationDashboard.jsx';

export default function TenderWorkflowPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const tenderId = decodeURIComponent(id);
  return <PageContainer title="Tender Evaluation Workflow" subtitle="Read-only workflow visibility and links to the authoritative modules.">
    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 20 }}>
      <button type="button" onClick={() => navigate(`/tenders/${encodeURIComponent(tenderId)}`)}>Requirements</button>
      <button type="button" onClick={() => navigate(`/tenders/${encodeURIComponent(tenderId)}/dashboard`)}>Evaluation dashboard</button>
      <button type="button" onClick={() => navigate('/documents')}>Documents</button>
      <button type="button" onClick={() => navigate('/audit')}>Audit trail</button>
    </div>
    <TenderEvaluationDashboard tenderId={tenderId} />
  </PageContainer>;
}
