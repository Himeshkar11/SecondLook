import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import PageContainer from '../components/layout/PageContainer.jsx';
import Button from '../components/common/Button.jsx';
import TenderEvaluationDashboard from '../components/dashboard/TenderEvaluationDashboard.jsx';

/**
 * TenderWorkflowPage (Milestone 10)
 * Officer operational workflow view for a specific tender.
 * Displays evaluation stats, bidder evaluations table, and requirement issues.
 * Provides onOpenBidder to drill down into the BidderDetailPage & OfficerReviewPanel.
 */
export default function TenderWorkflowPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const tenderId = decodeURIComponent(id || '');

  const handleOpenBidder = (bidder) => {
    if (!bidder || !bidder.bidder_id) return;
    navigate(`/officer/bidders/${encodeURIComponent(bidder.bidder_id)}?tender_id=${encodeURIComponent(tenderId)}`);
  };

  return (
    <PageContainer
      title="Tender Evaluation Workflow"
      subtitle="Operational compliance oversight, statutory verification traces, and officer reviews."
      actions={
        <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
          <Button variant="ghost" size="sm" onClick={() => navigate('/officer/dashboard')}>
            ← Back to Overview
          </Button>
          <Button variant="secondary" size="sm" onClick={() => navigate(`/officer/tenders/${encodeURIComponent(tenderId)}`)}>
            Requirements
          </Button>
          <Button variant="secondary" size="sm" onClick={() => navigate('/officer/audit')}>
            Audit Trail
          </Button>
        </div>
      }
    >
      <TenderEvaluationDashboard
        tenderId={tenderId}
        onOpenBidder={handleOpenBidder}
      />
    </PageContainer>
  );
}
