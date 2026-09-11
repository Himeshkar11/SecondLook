import React from 'react';
import { useNavigate } from 'react-router-dom';
import PageContainer from '../components/layout/PageContainer.jsx';
import EmptyState from '../components/common/EmptyState.jsx';

/**
 * Standardized placeholder page for future milestone views:
 * Login and any deferred modules
 */
export default function PlaceholderPage({ title, description }) {
  const navigate = useNavigate();
  return (
    <PageContainer
      title={title}
      subtitle={description || `Statutory management and records for ${title}`}
    >
      <EmptyState
        title={`${title} Module`}
        description={`The ${title} workflow is scheduled for implementation in upcoming milestones. You can navigate the live prototype via the Dashboard.`}
        actionLabel="Back to Dashboard"
        onAction={() => navigate('/dashboard')}
      />
    </PageContainer>
  );
}
