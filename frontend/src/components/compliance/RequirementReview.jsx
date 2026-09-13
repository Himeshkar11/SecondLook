/**
 * RequirementReview — Task 16
 * Per-requirement card showing compliance result + review controls + evidence link.
 * Reuses the existing Task 15 EvidenceTraceModal via onViewEvidence callback.
 */

import React, { useState } from "react";
import ReviewStatusBadge from "./ReviewStatusBadge";

const COMPLIANCE_COLORS = {
  PASS: { text: "#166534", bg: "#dcfce7", border: "#bbf7d0", icon: "✓" },
  FAIL: { text: "#991b1b", bg: "#fee2e2", border: "#fecaca", icon: "✕" },
  PARTIAL: { text: "#92400e", bg: "#fef3c7", border: "#fde68a", icon: "⚠" },
  NOT_VERIFIED: { text: "#6b21a8", bg: "#f3e8ff", border: "#e9d5ff", icon: "!" },
  NOT_APPLICABLE: { text: "#6b7280", bg: "#f9fafb", border: "#e5e7eb", icon: "—" },
};

export default function RequirementReview({
  item,
  onMarkReviewed,
  onMarkFlagged,
  onViewEvidence,
  disabled = false,
}) {
  const [comment, setComment] = useState(item.review?.officer_comment || "");
  const [showComment, setShowComment] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const reviewStatus = item.review?.review_status || "NOT_REVIEWED";
  const isReviewed = reviewStatus !== "NOT_REVIEWED";
  const cfg = COMPLIANCE_COLORS[item.compliance_status] || COMPLIANCE_COLORS.NOT_VERIFIED;

  const handleMark = async (status) => {
    setSaving(true);
    setError(null);
    try {
      await (status === "REVIEWED" ? onMarkReviewed : onMarkFlagged)(
        item.requirement_result_id,
        comment || null
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      style={{
        border: `1px solid ${cfg.border}`,
        borderLeft: `4px solid ${cfg.text}`,
        borderRadius: "6px",
        padding: "16px",
        marginBottom: "12px",
        background: "#fff",
      }}
    >
      {/* Header row */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "12px" }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                width: "22px",
                height: "22px",
                borderRadius: "50%",
                background: cfg.bg,
                color: cfg.text,
                fontSize: "0.75rem",
                fontWeight: 700,
                border: `1px solid ${cfg.border}`,
                flexShrink: 0,
              }}
            >
              {cfg.icon}
            </span>
            <span style={{ fontWeight: 600, color: "#111827" }}>{item.requirement_title}</span>
            <span style={{ fontSize: "0.7rem", color: "#9ca3af", fontFamily: "monospace" }}>
              {item.requirement_code}
            </span>
            {item.mandatory && (
              <span style={{ fontSize: "0.65rem", color: "#991b1b", background: "#fee2e2", padding: "1px 6px", borderRadius: "10px", fontWeight: 600 }}>
                MANDATORY
              </span>
            )}
          </div>

          {/* Compliance status */}
          <div style={{ marginTop: "6px", display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
            <span
              style={{
                fontSize: "0.75rem",
                fontWeight: 700,
                color: cfg.text,
                background: cfg.bg,
                padding: "2px 8px",
                borderRadius: "4px",
                border: `1px solid ${cfg.border}`,
              }}
            >
              {item.compliance_status}
            </span>
            {item.explanation && (
              <span style={{ fontSize: "0.8rem", color: "#6b7280" }}>{item.explanation}</span>
            )}
          </div>

          {/* Existing review comment */}
          {item.review?.officer_comment && (
            <div style={{ marginTop: "8px", fontSize: "0.8rem", color: "#374151", background: "#f9fafb", padding: "6px 10px", borderRadius: "4px", borderLeft: "3px solid #d1d5db" }}>
              <strong>Officer Comment:</strong> {item.review.officer_comment}
            </div>
          )}
        </div>

        {/* Review status badge */}
        <ReviewStatusBadge status={reviewStatus} />
      </div>

      {/* Actions row */}
      <div style={{ marginTop: "12px", display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
        {/* View Evidence — reuses Task 15 */}
        <button
          onClick={() => onViewEvidence && onViewEvidence(item)}
          style={{
            padding: "5px 12px",
            fontSize: "0.78rem",
            fontWeight: 500,
            color: "#1d4ed8",
            background: "#eff6ff",
            border: "1px solid #bfdbfe",
            borderRadius: "5px",
            cursor: "pointer",
          }}
        >
          View Evidence
        </button>

        {!disabled && (
          <>
            {/* Add/edit comment toggle */}
            <button
              onClick={() => setShowComment((v) => !v)}
              style={{
                padding: "5px 12px",
                fontSize: "0.78rem",
                fontWeight: 500,
                color: "#374151",
                background: "#f9fafb",
                border: "1px solid #d1d5db",
                borderRadius: "5px",
                cursor: "pointer",
              }}
            >
              {showComment ? "Hide Comment" : "Add Comment"}
            </button>

            {reviewStatus !== "REVIEWED" && (
              <button
                onClick={() => handleMark("REVIEWED")}
                disabled={saving}
                style={{
                  padding: "5px 12px",
                  fontSize: "0.78rem",
                  fontWeight: 600,
                  color: "#166534",
                  background: "#dcfce7",
                  border: "1px solid #bbf7d0",
                  borderRadius: "5px",
                  cursor: saving ? "not-allowed" : "pointer",
                  opacity: saving ? 0.6 : 1,
                }}
              >
                ✓ Mark Reviewed
              </button>
            )}

            {reviewStatus !== "FLAGGED" && (
              <button
                onClick={() => handleMark("FLAGGED")}
                disabled={saving}
                style={{
                  padding: "5px 12px",
                  fontSize: "0.78rem",
                  fontWeight: 600,
                  color: "#92400e",
                  background: "#fef3c7",
                  border: "1px solid #fde68a",
                  borderRadius: "5px",
                  cursor: saving ? "not-allowed" : "pointer",
                  opacity: saving ? 0.6 : 1,
                }}
              >
                ⚑ Flag
              </button>
            )}
          </>
        )}
      </div>

      {/* Comment input */}
      {showComment && !disabled && (
        <div style={{ marginTop: "10px" }}>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Add officer comment for this requirement…"
            rows={2}
            style={{
              width: "100%",
              padding: "8px 10px",
              fontSize: "0.82rem",
              border: "1px solid #d1d5db",
              borderRadius: "5px",
              resize: "vertical",
              boxSizing: "border-box",
            }}
          />
        </div>
      )}

      {error && (
        <div style={{ marginTop: "8px", padding: "6px 10px", background: "#fee2e2", color: "#991b1b", borderRadius: "4px", fontSize: "0.8rem" }}>
          {error}
        </div>
      )}
    </div>
  );
}
