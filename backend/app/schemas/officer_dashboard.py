"""Pydantic schemas for Officer Operations Dashboard (Milestone 10).

Provides structured data transfer models for high-level procurement metrics,
tender progress rows, and itemized attention notices.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class OfficerDashboardOverview(BaseModel):
    """Aggregate statistics across all authorized procurement tenders."""

    active_tenders: int = Field(..., description="Count of tenders currently in ACTIVE status")
    total_tenders: int = Field(default=0, description="Total count of authorized tenders")
    bids_received: int = Field(..., description="Total count of bids submitted or received across tenders")
    evaluations_pending: int = Field(..., description="Count of evaluations pending or currently processing")
    reviews_requiring_attention: int = Field(..., description="Count of reviews or evaluations requiring officer attention")


class OfficerTenderRow(BaseModel):
    """Operational summary of a single tender for the officer dashboard table."""

    id: str = Field(..., description="Unique UUID string of the tender")
    reference_number: str = Field(..., description="Public tender reference number e.g. GEM/2026/B/...")
    title: str = Field(..., description="Title of the tender procurement")
    status: str = Field(..., description="Current tender status e.g. ACTIVE, DRAFT, UNDER_REVIEW, CLOSED")
    bidders_count: int = Field(..., description="Total bidders associated with this tender")
    bids_count: int = Field(..., description="Total bid submissions recorded for this tender")
    evaluated_count: int = Field(..., description="Count of unique bidders evaluated for this tender")
    evaluations_completed: int = Field(..., description="Count of completed compliance evaluations")
    evaluations_processing: int = Field(..., description="Count of compliance evaluations in progress")
    attention_required: bool = Field(..., description="Whether this tender has items requiring officer attention")
    attention_reasons: List[str] = Field(default_factory=list, description="Specific reasons requiring officer attention")
    created_at: Optional[str] = Field(None, description="ISO timestamp when tender was created")
    updated_at: Optional[str] = Field(None, description="ISO timestamp when tender was last updated")


class OfficerAttentionItem(BaseModel):
    """Discrete, actionable item requiring procurement officer review or decision."""

    id: str = Field(..., description="Unique identifier of this attention notice")
    type: str = Field(..., description="Category: REQUIREMENT_APPROVAL, EVALUATION_PROCESSING, EVALUATION_FAILED, MANDATORY_ISSUE, REVIEW_PENDING")
    tender_id: str = Field(..., description="UUID string of the associated tender")
    tender_title: str = Field(..., description="Title of the tender")
    tender_reference: str = Field(..., description="Reference number of the tender")
    bidder_id: Optional[str] = Field(None, description="UUID string of the associated bidder if applicable")
    bidder_name: Optional[str] = Field(None, description="Legal name of the bidder if applicable")
    severity: str = Field(..., description="Visual severity level: warning, danger, info")
    message: str = Field(..., description="Factual description of the item requiring attention")
    action_url: str = Field(..., description="Relative navigation URL for officer action")
    action_label: str = Field(..., description="Action button label e.g. 'Review Requirements', 'Inspect Evaluation'")
    created_at: Optional[str] = Field(None, description="Timestamp of the originating event or entity")


class OfficerDashboardResponse(BaseModel):
    """Top-level response payload for the Officer Operations Dashboard."""

    overview: OfficerDashboardOverview = Field(..., description="Summary operational metrics")
    tenders: List[OfficerTenderRow] = Field(default_factory=list, description="List of authorized tender rows")
    attention_items: List[OfficerAttentionItem] = Field(default_factory=list, description="Itemized list of attention notices")
