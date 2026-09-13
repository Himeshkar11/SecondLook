import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import PageContainer from '../components/layout/PageContainer.jsx';
import Badge from '../components/common/Badge.jsx';
import Button from '../components/common/Button.jsx';
import Loading from '../components/common/Loading.jsx';
import EmptyState from '../components/common/EmptyState.jsx';
import Modal from '../components/common/Modal.jsx';
import { getTenderById, getTenderBidders } from '../services/tenderService.js';
import {
  getTenderRequirements,
  createTenderRequirement,
  extractTenderRequirements,
  approveTenderRequirement,
  rejectTenderRequirement,
  updateTenderRequirement,
} from '../services/complianceService.js';

/**
 * TenderDetailPage — Dynamic Supabase-backed tender detail view with Task 12 requirement management.
 * 
 * Features:
 * - Approved Requirements (evaluated by Compliance Engine)
 * - AI Suggestions & Pending Review (strict officer approval gate)
 * - AI Requirement Extraction modal
 * - Manual Requirement creation modal
 * - Inline review actions: Approve, Edit, Reject
 * - Traceability snippet display
 */
export default function TenderDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const tenderId = decodeURIComponent(id);

  const [tender, setTender] = useState(null);
  const [bidders, setBidders] = useState([]);
  const [requirements, setRequirements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notFound, setNotFound] = useState(false);
  const [biddersLoading, setBiddersLoading] = useState(false);
  const [requirementsLoading, setRequirementsLoading] = useState(false);

  // Tab: 'APPROVED', 'PENDING', 'ALL'
  const [reqTab, setReqTab] = useState('APPROVED');
  const [actionLoadingId, setActionLoadingId] = useState(null);

  // Modals state
  const [isExtractModalOpen, setIsExtractModalOpen] = useState(false);
  const [extractText, setExtractText] = useState('');
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractError, setExtractError] = useState(null);

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [newReq, setNewReq] = useState({
    title: '',
    code: '',
    type: 'GST',
    mandatory: true,
    description: '',
    rule_type: 'STATUS_EQUALS',
    field: 'status',
    operator: 'EQUALS',
    expected_value: 'ACTIVE',
  });
  const [isCreating, setIsCreating] = useState(false);
  const [createError, setCreateError] = useState(null);

  const [editingReq, setEditingReq] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateError, setUpdateError] = useState(null);

  const fetchRequirements = useCallback(async () => {
    setRequirementsLoading(true);
    try {
      const reqData = await getTenderRequirements(tenderId);
      setRequirements(Array.isArray(reqData) ? reqData : []);
    } catch {
      setRequirements([]);
    } finally {
      setRequirementsLoading(false);
    }
  }, [tenderId]);

  const fetchTenderDetails = useCallback(async () => {
    setLoading(true);
    setError(null);
    setNotFound(false);
    setTender(null);
    setBidders([]);
    setRequirements([]);

    try {
      const data = await getTenderById(tenderId);
      setTender(data);

      await fetchRequirements();

      setBiddersLoading(true);
      try {
        const bidderData = await getTenderBidders(tenderId);
        setBidders(bidderData.items || []);
      } catch {
        setBidders([]);
      } finally {
        setBiddersLoading(false);
      }
    } catch (err) {
      if (err.status === 404) {
        setNotFound(true);
      } else {
        setError(err.message || 'Unable to load tender details. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  }, [tenderId, fetchRequirements]);

  useEffect(() => {
    fetchTenderDetails();
  }, [fetchTenderDetails]);

  // Review Actions
  const handleApprove = async (reqId) => {
    setActionLoadingId(reqId);
    try {
      await approveTenderRequirement(reqId);
      await fetchRequirements();
    } catch (err) {
      alert(`Approval failed: ${err.message || 'Unknown error'}`);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleReject = async (reqId) => {
    if (!window.confirm('Are you sure you want to reject this requirement? It will not be evaluated in compliance.')) {
      return;
    }
    setActionLoadingId(reqId);
    try {
      await rejectTenderRequirement(reqId);
      await fetchRequirements();
    } catch (err) {
      alert(`Rejection failed: ${err.message || 'Unknown error'}`);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleExtractSubmit = async (e) => {
    e.preventDefault();
    if (!extractText.trim()) {
      setExtractError('Please enter tender text or clauses to extract from.');
      return;
    }
    setIsExtracting(true);
    setExtractError(null);
    try {
      await extractTenderRequirements(tenderId, { text: extractText });
      await fetchRequirements();
      setIsExtractModalOpen(false);
      setExtractText('');
      setReqTab('PENDING'); // Switch to pending tab so officer can review newly suggested rules
    } catch (err) {
      setExtractError(err.message || 'Failed to extract requirements.');
    } finally {
      setIsExtracting(false);
    }
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    if (!newReq.title.trim()) {
      setCreateError('Requirement title is required.');
      return;
    }
    setIsCreating(true);
    setCreateError(null);
    try {
      const payload = {
        title: newReq.title,
        code: newReq.code || undefined,
        type: newReq.type,
        mandatory: newReq.mandatory,
        description: newReq.description,
        rule_type: newReq.rule_type,
        parameters: newReq.rule_type ? {
          source: newReq.type,
          field: newReq.field,
          operator: newReq.operator,
          expected_value: newReq.expected_value,
        } : null,
        status: 'UNDER_REVIEW',
      };
      await createTenderRequirement(tenderId, payload);
      await fetchRequirements();
      setIsCreateModalOpen(false);
      setNewReq({
        title: '',
        code: '',
        type: 'GST',
        mandatory: true,
        description: '',
        rule_type: 'STATUS_EQUALS',
        field: 'status',
        operator: 'EQUALS',
        expected_value: 'ACTIVE',
      });
      setReqTab('PENDING');
    } catch (err) {
      setCreateError(err.message || 'Failed to create requirement.');
    } finally {
      setIsCreating(false);
    }
  };

  const handleStartEdit = (req) => {
    setEditingReq(req);
    setEditForm({
      title: req.title,
      description: req.description || '',
      type: req.type,
      mandatory: req.mandatory,
      rule_type: req.rule_type || '',
    });
    setUpdateError(null);
  };

  const handleUpdateSubmit = async (e) => {
    e.preventDefault();
    if (!editingReq) return;
    setIsUpdating(true);
    setUpdateError(null);
    try {
      await updateTenderRequirement(editingReq.id, editForm);
      await fetchRequirements();
      setEditingReq(null);
    } catch (err) {
      setUpdateError(err.message || 'Failed to update requirement.');
    } finally {
      setIsUpdating(false);
    }
  };

  // Badges
  const getStatusBadge = (status) => {
    const s = (status || '').toUpperCase();
    switch (s) {
      case 'ACTIVE': return <Badge variant="success">Active</Badge>;
      case 'REVIEW':
      case 'UNDER_REVIEW': return <Badge variant="warning">Under Review</Badge>;
      case 'PENDING':
      case 'DRAFT': return <Badge variant="info">Pending</Badge>;
      case 'CLOSED': return <Badge variant="neutral">Closed</Badge>;
      default: return <Badge variant="neutral">{status}</Badge>;
    }
  };

  const getRiskBadge = (risk) => {
    switch ((risk || 'LOW').toUpperCase()) {
      case 'LOW': return <Badge variant="success">Low Risk</Badge>;
      case 'MEDIUM': return <Badge variant="warning">Med Risk</Badge>;
      case 'HIGH': return <Badge variant="danger">High Risk</Badge>;
      default: return <Badge variant="neutral">{risk}</Badge>;
    }
  };

  const getBidderStatusBadge = (status) => {
    switch ((status || '').toUpperCase()) {
      case 'VERIFIED': return <Badge variant="success">Verified</Badge>;
      case 'PENDING': return <Badge variant="info">Pending</Badge>;
      case 'FLAGGED': return <Badge variant="danger">Flagged</Badge>;
      default: return <Badge variant="neutral">{status}</Badge>;
    }
  };

  const getRequirementStatusBadge = (status) => {
    switch ((status || 'APPROVED').toUpperCase()) {
      case 'APPROVED':
        return <Badge variant="success">Approved</Badge>;
      case 'AI_SUGGESTED':
        return <Badge variant="info">AI Suggested</Badge>;
      case 'UNDER_REVIEW':
        return <Badge variant="warning">Under Review</Badge>;
      case 'DRAFT':
        return <Badge variant="neutral">Draft</Badge>;
      case 'REJECTED':
        return <Badge variant="danger">Rejected</Badge>;
      case 'ARCHIVED':
        return <Badge variant="neutral">Archived</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };

  // Filter requirements by tab
  const approvedRequirements = requirements.filter(r => (r.status || 'APPROVED') === 'APPROVED');
  const pendingRequirements = requirements.filter(r => ['AI_SUGGESTED', 'UNDER_REVIEW', 'DRAFT'].includes(r.status));
  const rejectedOrArchived = requirements.filter(r => ['REJECTED', 'ARCHIVED'].includes(r.status));

  const displayedRequirements = reqTab === 'APPROVED'
    ? approvedRequirements
    : reqTab === 'PENDING'
    ? pendingRequirements
    : requirements;

  if (loading) {
    return (
      <PageContainer title="Tender Details">
        <div
          style={{
            backgroundColor: 'var(--color-bg-card)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--color-border)',
            padding: 'var(--space-8)',
          }}
        >
          <Loading message="Loading tender details..." />
        </div>
      </PageContainer>
    );
  }

  if (notFound) {
    return (
      <PageContainer title="Tender Not Found">
        <EmptyState
          title="Tender not found"
          description="The requested tender could not be found in the database."
          actionLabel="Back to Tenders"
          onAction={() => navigate('/tenders')}
        />
      </PageContainer>
    );
  }

  return (
    <PageContainer
      title={tender?.title || 'Tender Details'}
      subtitle={tender?.tender_reference ? `Reference: ${tender.tender_reference}` : undefined}
      actions={
        <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
          <Button variant="secondary" size="sm" onClick={() => navigate('/tenders')}>
            ← All Tenders
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsExtractModalOpen(true)}
            style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-1)' }}
          >
            ✨ Extract with AI
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setIsCreateModalOpen(true)}
          >
            + Add Requirement
          </Button>
        </div>
      }
    >
      {error && (
        <div
          style={{
            backgroundColor: 'var(--color-danger-bg, #fef2f2)',
            color: 'var(--color-danger, #dc2626)',
            padding: 'var(--space-3) var(--space-4)',
            borderRadius: 'var(--radius-md)',
            marginBottom: 'var(--space-4)',
            fontSize: 'var(--font-size-sm)',
            border: '1px solid var(--color-danger-border, #fecaca)',
          }}
        >
          {error}
        </div>
      )}

      {/* Tender Details Card */}
      <div
        style={{
          backgroundColor: 'var(--color-bg-card)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--color-border)',
          boxShadow: 'var(--shadow-xs)',
          padding: 'var(--space-5)',
          marginBottom: 'var(--space-6)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 'var(--space-4)' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-2)' }}>
              {getStatusBadge(tender.status)}
              {tender.tender_type && <Badge variant="neutral">{tender.tender_type}</Badge>}
            </div>
            <h2 style={{ fontSize: 'var(--font-size-xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)' }}>
              {tender.title}
            </h2>
            <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', marginTop: 'var(--space-1)', fontFamily: 'var(--font-family-mono)' }}>
              ID: {tender.id}
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Estimated Value
            </div>
            <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)' }}>
              {tender.estimated_value ? `₹${Number(tender.estimated_value).toLocaleString('en-IN')}` : 'Not Specified'}
            </div>
          </div>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: 'var(--space-4)',
            marginTop: 'var(--space-5)',
            paddingTop: 'var(--space-4)',
            borderTop: '1px solid var(--color-border-subtle)',
          }}
        >
          <div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>Authority / Department</div>
            <div style={{ fontWeight: 'var(--font-weight-medium)', color: 'var(--color-text-primary)', marginTop: 'var(--space-1)' }}>
              {tender.department || tender.authority || '—'}
            </div>
          </div>
          <div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>Submission Deadline</div>
            <div style={{ fontWeight: 'var(--font-weight-medium)', color: 'var(--color-text-primary)', marginTop: 'var(--space-1)' }}>
              {tender.submission_deadline ? new Date(tender.submission_deadline).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : '—'}
            </div>
          </div>
          <div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>Active Requirements</div>
            <div style={{ fontWeight: 'var(--font-weight-medium)', color: 'var(--color-success)', marginTop: 'var(--space-1)' }}>
              {approvedRequirements.length} Approved ({pendingRequirements.length} Pending Review)
            </div>
          </div>
          <div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>Total Bidders</div>
            <div style={{ fontWeight: 'var(--font-weight-medium)', color: 'var(--color-text-primary)', marginTop: 'var(--space-1)' }}>
              {bidders.length} Submitted
            </div>
          </div>
        </div>

        <div style={{ marginTop: 'var(--space-4)', paddingTop: 'var(--space-4)', borderTop: '1px solid var(--color-border-subtle)' }}>
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 'var(--space-2)' }}>
            Scope of Work
          </div>
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
            {tender.description || 'No description available.'}
          </p>
        </div>
      </div>

      {/* Statutory Tender Requirements Section (Task 11 & Task 12) */}
      <div
        style={{
          backgroundColor: 'var(--color-bg-card)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--color-border)',
          boxShadow: 'var(--shadow-xs)',
          overflow: 'hidden',
          marginBottom: 'var(--space-6)',
        }}
      >
        {/* Section Header */}
        <div
          style={{
            padding: 'var(--space-4) var(--space-5)',
            borderBottom: '1px solid var(--color-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: 'var(--space-3)',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <h3 style={{ fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-primary)' }}>
                Tender Statutory Requirements & Verification Rules
              </h3>
            </div>
            <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: '2px' }}>
              Only <strong style={{ color: 'var(--color-success)' }}>Approved</strong> requirements enter the Compliance Engine. AI suggestions must be reviewed and approved by an officer.
            </p>
          </div>
          <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
            <Button
              variant="primary"
              size="sm"
              onClick={() => setIsExtractModalOpen(true)}
              style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-1)' }}
            >
              ✨ Extract with AI
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setIsCreateModalOpen(true)}
            >
              + Add Rule
            </Button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div
          style={{
            display: 'flex',
            gap: 'var(--space-4)',
            padding: '0 var(--space-5)',
            borderBottom: '1px solid var(--color-border)',
            backgroundColor: 'var(--color-bg-subtle)',
          }}
        >
          <button
            onClick={() => setReqTab('APPROVED')}
            style={{
              padding: 'var(--space-3) 0',
              border: 'none',
              background: 'none',
              cursor: 'pointer',
              fontWeight: reqTab === 'APPROVED' ? 'var(--font-weight-bold)' : 'var(--font-weight-medium)',
              color: reqTab === 'APPROVED' ? 'var(--color-primary)' : 'var(--color-text-muted)',
              borderBottom: reqTab === 'APPROVED' ? '2px solid var(--color-primary)' : '2px solid transparent',
              fontSize: 'var(--font-size-sm)',
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-2)',
            }}
          >
            Approved ({approvedRequirements.length})
            <span style={{ fontSize: '10px', background: 'var(--color-success-bg, #dcfce7)', color: 'var(--color-success, #15803d)', padding: '2px 6px', borderRadius: '10px' }}>
              Engine Active
            </span>
          </button>

          <button
            onClick={() => setReqTab('PENDING')}
            style={{
              padding: 'var(--space-3) 0',
              border: 'none',
              background: 'none',
              cursor: 'pointer',
              fontWeight: reqTab === 'PENDING' ? 'var(--font-weight-bold)' : 'var(--font-weight-medium)',
              color: reqTab === 'PENDING' ? 'var(--color-primary)' : 'var(--color-text-muted)',
              borderBottom: reqTab === 'PENDING' ? '2px solid var(--color-primary)' : '2px solid transparent',
              fontSize: 'var(--font-size-sm)',
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-2)',
            }}
          >
            AI Suggestions & Pending Review ({pendingRequirements.length})
            {pendingRequirements.length > 0 && (
              <span style={{ fontSize: '10px', background: 'var(--color-warning-bg, #fef3c7)', color: 'var(--color-warning, #b45309)', padding: '2px 6px', borderRadius: '10px' }}>
                Action Needed
              </span>
            )}
          </button>

          <button
            onClick={() => setReqTab('ALL')}
            style={{
              padding: 'var(--space-3) 0',
              border: 'none',
              background: 'none',
              cursor: 'pointer',
              fontWeight: reqTab === 'ALL' ? 'var(--font-weight-bold)' : 'var(--font-weight-medium)',
              color: reqTab === 'ALL' ? 'var(--color-primary)' : 'var(--color-text-muted)',
              borderBottom: reqTab === 'ALL' ? '2px solid var(--color-primary)' : '2px solid transparent',
              fontSize: 'var(--font-size-sm)',
            }}
          >
            All ({requirements.length})
          </button>
        </div>

        {/* Requirements Table */}
        {requirementsLoading ? (
          <div style={{ padding: 'var(--space-6)' }}>
            <Loading message="Loading tender requirements..." size="sm" />
          </div>
        ) : displayedRequirements.length === 0 ? (
          <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>
            {reqTab === 'APPROVED'
              ? 'No requirements have been approved yet. Extract candidates or add rules and approve them to activate compliance.'
              : reqTab === 'PENDING'
              ? 'No pending AI suggestions or rules under review.'
              : 'No statutory requirements configured for this tender.'}
          </div>
        ) : (
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
                  <th style={{ padding: 'var(--space-3) var(--space-5)' }}>Code</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Title & Details</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Status</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Category</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Mandatory</th>
                  <th style={{ padding: 'var(--space-3) var(--space-5)' }}>Deterministic Rule</th>
                  <th style={{ padding: 'var(--space-3) var(--space-5)', textAlign: 'right' }}>Officer Actions</th>
                </tr>
              </thead>
              <tbody>
                {displayedRequirements.map((req, index) => {
                  const isApproved = (req.status || 'APPROVED') === 'APPROVED';
                  const isPending = ['AI_SUGGESTED', 'UNDER_REVIEW', 'DRAFT'].includes(req.status);
                  const isRejected = req.status === 'REJECTED';

                  return (
                    <tr
                      key={req.id || req.code}
                      style={{
                        borderBottom: index === displayedRequirements.length - 1 ? 'none' : '1px solid var(--color-border-subtle)',
                        backgroundColor: req.status === 'AI_SUGGESTED' ? 'rgba(99, 102, 241, 0.03)' : 'transparent',
                      }}
                    >
                      <td style={{ padding: 'var(--space-3) var(--space-5)', fontFamily: 'var(--font-family-mono)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-primary)' }}>
                        {req.code}
                      </td>
                      <td style={{ padding: 'var(--space-3) var(--space-4)', maxWidth: '300px' }}>
                        <div style={{ fontWeight: 'var(--font-weight-medium)', color: 'var(--color-text-primary)' }}>
                          {req.title}
                        </div>
                        {req.description && (
                          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: '2px' }}>
                            {req.description}
                          </div>
                        )}
                        {/* Traceability snippet */}
                        {req.source_text && (
                          <div
                            style={{
                              marginTop: 'var(--space-2)',
                              padding: 'var(--space-2)',
                              backgroundColor: 'rgba(0,0,0,0.03)',
                              borderRadius: 'var(--radius-sm)',
                              borderLeft: '2px solid var(--color-primary)',
                              fontSize: 'var(--font-size-xs)',
                              color: 'var(--color-text-secondary)',
                            }}
                          >
                            <span style={{ fontWeight: 'var(--font-weight-semibold)' }}>Source: </span>
                            &ldquo;{req.source_text}&rdquo;
                            {(req.source_page || req.source_section) && (
                              <div style={{ fontSize: '10px', color: 'var(--color-text-muted)', marginTop: '2px' }}>
                                {req.source_page ? `Page ${req.source_page}` : ''}
                                {req.source_page && req.source_section ? ' • ' : ''}
                                {req.source_section ? `Section: ${req.source_section}` : ''}
                              </div>
                            )}
                          </div>
                        )}
                      </td>
                      <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                        {getRequirementStatusBadge(req.status)}
                      </td>
                      <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                        <Badge variant="neutral">{req.type}</Badge>
                      </td>
                      <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                        {req.mandatory ? (
                          <Badge variant="warning">Mandatory</Badge>
                        ) : (
                          <Badge variant="neutral">Optional</Badge>
                        )}
                      </td>
                      <td style={{ padding: 'var(--space-3) var(--space-5)', fontSize: 'var(--font-size-xs)', fontFamily: 'var(--font-family-mono)', color: 'var(--color-text-secondary)' }}>
                        {(req.rule_config && req.rule_config.length > 0) ? (
                          req.rule_config.map((rc, i) => (
                            <div key={i}>
                              {rc.source}.{rc.field} {rc.operator} {rc.expected_value ? `"${rc.expected_value}"` : ''}
                            </div>
                          ))
                        ) : req.rule_type ? (
                          <div>{req.rule_type}</div>
                        ) : (
                          <span style={{ color: 'var(--color-text-muted)' }}>Manual Verification</span>
                        )}
                      </td>
                      <td style={{ padding: 'var(--space-3) var(--space-5)', textAlign: 'right' }}>
                        <div style={{ display: 'flex', gap: 'var(--space-1)', justifyContent: 'flex-end' }}>
                          {isPending && (
                            <Button
                              variant="success"
                              size="xs"
                              disabled={actionLoadingId === req.id}
                              onClick={() => handleApprove(req.id)}
                            >
                              {actionLoadingId === req.id ? '…' : '✓ Approve'}
                            </Button>
                          )}
                          <Button
                            variant="secondary"
                            size="xs"
                            onClick={() => handleStartEdit(req)}
                          >
                            ✎ Edit
                          </Button>
                          {!isRejected && (
                            <Button
                              variant="danger"
                              size="xs"
                              disabled={actionLoadingId === req.id}
                              onClick={() => handleReject(req.id)}
                            >
                              ✕ Reject
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Submitted Bidders Table */}
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
            <h3 style={{ fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-primary)' }}>
              Submitted Bidders
            </h3>
            <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
              Bidders evaluated against the <strong style={{ color: 'var(--color-success)' }}>{approvedRequirements.length} approved</strong> tender requirements
            </p>
          </div>
          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
            {biddersLoading ? '…' : `${bidders.length} shown`}
          </span>
        </div>

        {biddersLoading ? (
          <div style={{ padding: 'var(--space-6)' }}>
            <Loading message="Loading bidders..." size="sm" />
          </div>
        ) : bidders.length === 0 ? (
          <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>
            No bidders have been associated with this tender.
          </div>
        ) : (
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
                  <th style={{ padding: 'var(--space-3) var(--space-5)' }}>Bidder Name</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)' }}>PAN</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)' }}>GSTIN</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'center' }}>Compliance</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Risk</th>
                  <th style={{ padding: 'var(--space-3) var(--space-4)' }}>Status</th>
                  <th style={{ padding: 'var(--space-3) var(--space-5)', textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {bidders.map((bidder, index) => (
                  <tr
                    key={bidder.id}
                    style={{
                      borderBottom: index === bidders.length - 1 ? 'none' : '1px solid var(--color-border-subtle)',
                      cursor: 'pointer',
                      transition: 'background-color var(--transition-fast)',
                    }}
                    onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'var(--color-bg-hover)'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; }}
                    onClick={() => navigate(`/bidders/${bidder.id}?tender_id=${encodeURIComponent(tenderId)}`)}
                  >
                    <td style={{ padding: 'var(--space-3) var(--space-5)' }}>
                      <div style={{ fontWeight: 'var(--font-weight-medium)', color: 'var(--color-text-primary)' }}>
                        {bidder.name || bidder.legal_name}
                      </div>
                      {bidder.msmeCategory && bidder.msmeCategory !== 'NOT APPLICABLE' && (
                        <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: '2px' }}>
                          MSME: {bidder.msmeCategory}
                        </div>
                      )}
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-4)', fontFamily: 'var(--font-family-mono)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                      {bidder.pan || bidder.pan_number || 'N/A'}
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-4)', fontFamily: 'var(--font-family-mono)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                      {bidder.gstin || bidder.gst_number || 'N/A'}
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'center' }}>
                      <span
                        style={{
                          fontWeight: 'var(--font-weight-bold)',
                          color: bidder.compliance >= 90 ? 'var(--color-success)' : bidder.compliance >= 70 ? 'var(--color-warning)' : 'var(--color-danger)',
                        }}
                      >
                        {bidder.compliance != null ? `${bidder.compliance}%` : '—'}
                      </span>
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                      {getRiskBadge(bidder.risk)}
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                      {getBidderStatusBadge(bidder.status)}
                    </td>
                    <td style={{ padding: 'var(--space-3) var(--space-5)', textAlign: 'right' }}>
                      <Button
                        variant="ghost"
                        size="sm"
                        style={{ color: 'var(--color-primary)' }}
                        onClick={(e) => { e.stopPropagation(); navigate(`/bidders/${bidder.id}?tender_id=${encodeURIComponent(tenderId)}`); }}
                      >
                        Review Compliance →
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal: AI Requirement Extraction */}
      <Modal
        isOpen={isExtractModalOpen}
        onClose={() => !isExtracting && setIsExtractModalOpen(false)}
        title="✨ Extract Requirements with AI"
        maxWidth="650px"
        footer={
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--space-2)' }}>
            <Button
              variant="secondary"
              disabled={isExtracting}
              onClick={() => setIsExtractModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              disabled={isExtracting || !extractText.trim()}
              onClick={handleExtractSubmit}
            >
              {isExtracting ? 'Extracting Candidate Rules...' : 'Extract Requirements'}
            </Button>
          </div>
        }
      >
        <div>
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-3)' }}>
            Paste the eligibility criteria or clauses from the tender notice. The AI extractor identifies statutory requirements and rule configurations.
          </p>

          <div
            style={{
              padding: 'var(--space-3)',
              backgroundColor: 'rgba(99, 102, 241, 0.08)',
              borderRadius: 'var(--radius-sm)',
              fontSize: 'var(--font-size-xs)',
              color: 'var(--color-text-primary)',
              marginBottom: 'var(--space-4)',
              borderLeft: '3px solid var(--color-primary)',
            }}
          >
            <strong>Strict Governance:</strong> All extracted rules are initially saved with status <code>AI_SUGGESTED</code>. The Compliance Engine will NOT evaluate them until you explicitly review and approve them.
          </div>

          {extractError && (
            <div
              style={{
                backgroundColor: 'var(--color-danger-bg, #fef2f2)',
                color: 'var(--color-danger, #dc2626)',
                padding: 'var(--space-2) var(--space-3)',
                borderRadius: 'var(--radius-sm)',
                fontSize: 'var(--font-size-xs)',
                marginBottom: 'var(--space-3)',
              }}
            >
              {extractError}
            </div>
          )}

          <label style={{ display: 'block', fontSize: 'var(--font-size-xs)', fontWeight: 'var(--font-weight-semibold)', marginBottom: 'var(--space-1)' }}>
            Tender Text / Clauses
          </label>
          <textarea
            rows={8}
            placeholder="e.g. 1. The bidder must possess an active GST registration certificate in the state of Tamil Nadu. 2. The bidder must submit a valid PAN card verified with Income Tax department..."
            value={extractText}
            onChange={(e) => setExtractText(e.target.value)}
            disabled={isExtracting}
            style={{
              width: '100%',
              padding: 'var(--space-2)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-border)',
              fontFamily: 'inherit',
              fontSize: 'var(--font-size-sm)',
            }}
          />
        </div>
      </Modal>

      {/* Modal: Add Manual Requirement */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => !isCreating && setIsCreateModalOpen(false)}
        title="Add Tender Requirement"
        maxWidth="550px"
        footer={
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--space-2)' }}>
            <Button variant="secondary" disabled={isCreating} onClick={() => setIsCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" disabled={isCreating || !newReq.title.trim()} onClick={handleCreateSubmit}>
              {isCreating ? 'Creating...' : 'Save Requirement'}
            </Button>
          </div>
        }
      >
        <div>
          {createError && (
            <div style={{ backgroundColor: '#fef2f2', color: '#dc2626', padding: '8px', borderRadius: '4px', fontSize: '12px', marginBottom: '12px' }}>
              {createError}
            </div>
          )}

          <div style={{ marginBottom: '12px' }}>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '4px' }}>Title *</label>
            <input
              type="text"
              placeholder="e.g. Active GST Registration"
              value={newReq.title}
              onChange={(e) => setNewReq({ ...newReq, title: e.target.value })}
              style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid var(--color-border)' }}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '4px' }}>Category</label>
              <select
                value={newReq.type}
                onChange={(e) => setNewReq({ ...newReq, type: e.target.value })}
                style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid var(--color-border)' }}
              >
                <option value="GST">GST</option>
                <option value="PAN">PAN</option>
                <option value="UDYAM">UDYAM</option>
                <option value="DOCUMENT">DOCUMENT</option>
                <option value="BLACKLISTING">BLACKLISTING</option>
                <option value="FINANCIAL">FINANCIAL</option>
                <option value="EXPERIENCE">EXPERIENCE</option>
                <option value="OTHER">OTHER</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '4px' }}>Requirement Code</label>
              <input
                type="text"
                placeholder="Auto-generated if empty"
                value={newReq.code}
                onChange={(e) => setNewReq({ ...newReq, code: e.target.value })}
                style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid var(--color-border)' }}
              />
            </div>
          </div>

          <div style={{ marginBottom: '12px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={newReq.mandatory}
                onChange={(e) => setNewReq({ ...newReq, mandatory: e.target.checked })}
              />
              <strong>Mandatory statutory requirement</strong>
            </label>
          </div>

          <div style={{ marginBottom: '12px' }}>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '4px' }}>Description</label>
            <textarea
              rows={2}
              placeholder="Requirement details..."
              value={newReq.description}
              onChange={(e) => setNewReq({ ...newReq, description: e.target.value })}
              style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid var(--color-border)' }}
            />
          </div>

          <div style={{ padding: '10px', backgroundColor: 'var(--color-bg-subtle)', borderRadius: '4px', fontSize: '12px' }}>
            <div style={{ fontWeight: 600, marginBottom: '6px' }}>Rule Evaluation Configuration</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '11px', color: 'var(--color-text-muted)' }}>Field</label>
                <input
                  type="text"
                  value={newReq.field}
                  onChange={(e) => setNewReq({ ...newReq, field: e.target.value })}
                  style={{ width: '100%', padding: '6px', borderRadius: '4px', border: '1px solid var(--color-border)' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '11px', color: 'var(--color-text-muted)' }}>Expected Value</label>
                <input
                  type="text"
                  value={newReq.expected_value}
                  onChange={(e) => setNewReq({ ...newReq, expected_value: e.target.value })}
                  style={{ width: '100%', padding: '6px', borderRadius: '4px', border: '1px solid var(--color-border)' }}
                />
              </div>
            </div>
          </div>
        </div>
      </Modal>

      {/* Modal: Edit Requirement */}
      {editingReq && (
        <Modal
          isOpen={true}
          onClose={() => !isUpdating && setEditingReq(null)}
          title={`Edit Requirement: ${editingReq.code}`}
          maxWidth="550px"
          footer={
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--space-2)' }}>
              <Button variant="secondary" disabled={isUpdating} onClick={() => setEditingReq(null)}>
                Cancel
              </Button>
              <Button variant="primary" disabled={isUpdating} onClick={handleUpdateSubmit}>
                {isUpdating ? 'Saving...' : 'Update Requirement'}
              </Button>
            </div>
          }
        >
          <div>
            {editingReq.status === 'APPROVED' && (
              <div
                style={{
                  padding: '8px',
                  backgroundColor: 'var(--color-warning-bg, #fef3c7)',
                  color: 'var(--color-warning, #b45309)',
                  borderRadius: '4px',
                  fontSize: '12px',
                  marginBottom: '12px',
                }}
              >
                ⚠️ <strong>Approval Demotion:</strong> Modifying this currently approved requirement will demote its status to <code>UNDER_REVIEW</code> to ensure proper procurement officer re-approval.
              </div>
            )}

            {updateError && (
              <div style={{ backgroundColor: '#fef2f2', color: '#dc2626', padding: '8px', borderRadius: '4px', fontSize: '12px', marginBottom: '12px' }}>
                {updateError}
              </div>
            )}

            <div style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '4px' }}>Title</label>
              <input
                type="text"
                value={editForm.title || ''}
                onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid var(--color-border)' }}
              />
            </div>

            <div style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '4px' }}>Description</label>
              <textarea
                rows={3}
                value={editForm.description || ''}
                onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid var(--color-border)' }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '4px' }}>Category</label>
                <select
                  value={editForm.type || 'GST'}
                  onChange={(e) => setEditForm({ ...editForm, type: e.target.value })}
                  style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid var(--color-border)' }}
                >
                  <option value="GST">GST</option>
                  <option value="PAN">PAN</option>
                  <option value="UDYAM">UDYAM</option>
                  <option value="DOCUMENT">DOCUMENT</option>
                  <option value="BLACKLISTING">BLACKLISTING</option>
                  <option value="FINANCIAL">FINANCIAL</option>
                  <option value="EXPERIENCE">EXPERIENCE</option>
                  <option value="OTHER">OTHER</option>
                </select>
              </div>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', cursor: 'pointer', marginTop: '16px' }}>
                  <input
                    type="checkbox"
                    checked={editForm.mandatory || false}
                    onChange={(e) => setEditForm({ ...editForm, mandatory: e.target.checked })}
                  />
                  <strong>Mandatory</strong>
                </label>
              </div>
            </div>
          </div>
        </Modal>
      )}
    </PageContainer>
  );
}
