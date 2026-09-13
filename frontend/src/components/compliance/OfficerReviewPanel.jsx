/**
 * OfficerReviewPanel — Task 16
 * Overall officer decision panel: decision radio, notes textarea, Save / Complete buttons.
 *
 * CRITICAL: Decision is strictly officer-initiated. The system never automatically
 * qualifies, disqualifies, rejects, or awards a bidder.
 */

import React, { useEffect, useState } from "react";

const DECISIONS = [
  { value: "QUALIFIED", label: "Qualified", color: "#166534" },
  { value: "NOT_QUALIFIED", label: "Not Qualified", color: "#991b1b" },
  { value: "REQUIRES_CLARIFICATION", label: "Requires Clarification", color: "#92400e" },
  { value: "WITHDRAWN", label: "Withdrawn", color: "#6b7280" },
  { value: "NO_DECISION", label: "No Decision (Defer)", color: "#9ca3af" },
];

const REVIEW_STATUS_STYLE = {
  PENDING: { color: "#6b7280", bg: "#f3f4f6" },
  IN_PROGRESS: { color: "#1d4ed8", bg: "#eff6ff" },
  COMPLETED: { color: "#166534", bg: "#dcfce7" },
};

export default function OfficerReviewPanel({
  review,
  onSaveDecision,
  onComplete,
  loading = false,
}) {
  const [decision, setDecision] = useState(review?.decision || "NO_DECISION");
  const [notes, setNotes] = useState(review?.notes || "");
  const [saving, setSaving] = useState(false);
  const [completing, setCompleting] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Sync when review prop changes (e.g. after refresh)
  useEffect(() => {
    setDecision(review?.decision || "NO_DECISION");
    setNotes(review?.notes || "");
  }, [review?.decision, review?.notes]);

  const isCompleted = review?.status === "COMPLETED";

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSuccessMsg(null);
    try {
      await onSaveDecision({ decision, notes: notes || undefined });
      setSuccessMsg("Decision saved successfully.");
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleComplete = async () => {
    setCompleting(true);
    setError(null);
    setSuccessMsg(null);
    try {
      await onComplete();
      setSuccessMsg("Review completed successfully.");
    } catch (err) {
      setError(err.message);
    } finally {
      setCompleting(false);
    }
  };

  const rsStyle = REVIEW_STATUS_STYLE[review?.status] || REVIEW_STATUS_STYLE.PENDING;

  return (
    <div
      style={{
        background: "#fff",
        border: "1px solid #e5e7eb",
        borderRadius: "8px",
        padding: "20px 24px",
      }}
    >
      {/* Panel header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px" }}>
        <h3 style={{ margin: 0, fontSize: "1rem", fontWeight: 600, color: "#111827" }}>
          Officer Decision
        </h3>
        {review?.status && (
          <span
            style={{
              fontSize: "0.75rem",
              fontWeight: 600,
              color: rsStyle.color,
              background: rsStyle.bg,
              padding: "3px 10px",
              borderRadius: "12px",
              border: `1px solid ${rsStyle.color}33`,
            }}
          >
            {review.status}
          </span>
        )}
      </div>

      {isCompleted ? (
        /* Completed — read-only display */
        <div>
          <p style={{ margin: "0 0 12px", fontSize: "0.85rem", color: "#374151" }}>
            This review has been completed. No further changes are allowed.
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            <div>
              <span style={{ fontSize: "0.75rem", color: "#6b7280", fontWeight: 500 }}>Decision: </span>
              <span style={{ fontWeight: 700, color: DECISIONS.find((d) => d.value === review.decision)?.color || "#374151" }}>
                {DECISIONS.find((d) => d.value === review.decision)?.label || review.decision}
              </span>
            </div>
            {review.notes && (
              <div>
                <span style={{ fontSize: "0.75rem", color: "#6b7280", fontWeight: 500 }}>Notes: </span>
                <span style={{ color: "#374151" }}>{review.notes}</span>
              </div>
            )}
            {review.completed_at && (
              <div>
                <span style={{ fontSize: "0.75rem", color: "#6b7280", fontWeight: 500 }}>Completed: </span>
                <span style={{ fontSize: "0.8rem", color: "#374151" }}>
                  {new Date(review.completed_at).toLocaleString()}
                </span>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* In-progress — editable */
        <>
          {/* Decision radio group */}
          <fieldset style={{ border: "none", margin: "0 0 16px", padding: 0 }}>
            <legend style={{ fontSize: "0.8rem", fontWeight: 600, color: "#374151", marginBottom: "10px" }}>
              Select Decision <span style={{ color: "#991b1b" }}>*</span>
            </legend>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {DECISIONS.map((d) => (
                <label
                  key={d.value}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "10px",
                    cursor: "pointer",
                    padding: "8px 12px",
                    borderRadius: "6px",
                    border: `1px solid ${decision === d.value ? d.color + "66" : "#e5e7eb"}`,
                    background: decision === d.value ? d.color + "0a" : "#fafafa",
                    transition: "all 0.15s",
                  }}
                >
                  <input
                    type="radio"
                    name="officer_decision"
                    value={d.value}
                    checked={decision === d.value}
                    onChange={() => setDecision(d.value)}
                    disabled={loading}
                    style={{ accentColor: d.color }}
                  />
                  <span style={{ fontWeight: decision === d.value ? 600 : 400, color: decision === d.value ? d.color : "#374151" }}>
                    {d.label}
                  </span>
                </label>
              ))}
            </div>
          </fieldset>

          {/* Notes */}
          <div style={{ marginBottom: "16px" }}>
            <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#374151", marginBottom: "6px" }}>
              Officer Notes
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add overall review notes…"
              rows={3}
              disabled={loading}
              style={{
                width: "100%",
                padding: "8px 12px",
                fontSize: "0.85rem",
                border: "1px solid #d1d5db",
                borderRadius: "5px",
                resize: "vertical",
                boxSizing: "border-box",
                color: "#111827",
              }}
            />
          </div>

          {/* Error / success */}
          {error && (
            <div style={{ marginBottom: "12px", padding: "8px 12px", background: "#fee2e2", color: "#991b1b", borderRadius: "5px", fontSize: "0.82rem" }}>
              {error}
            </div>
          )}
          {successMsg && (
            <div style={{ marginBottom: "12px", padding: "8px 12px", background: "#dcfce7", color: "#166534", borderRadius: "5px", fontSize: "0.82rem" }}>
              {successMsg}
            </div>
          )}

          {/* Action buttons */}
          <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
            <button
              onClick={handleSave}
              disabled={saving || loading}
              style={{
                padding: "8px 18px",
                fontSize: "0.85rem",
                fontWeight: 600,
                color: "#1d4ed8",
                background: "#eff6ff",
                border: "1px solid #bfdbfe",
                borderRadius: "6px",
                cursor: saving || loading ? "not-allowed" : "pointer",
                opacity: saving || loading ? 0.7 : 1,
              }}
            >
              {saving ? "Saving…" : "Save Decision"}
            </button>

            <button
              onClick={handleComplete}
              disabled={completing || loading}
              style={{
                padding: "8px 18px",
                fontSize: "0.85rem",
                fontWeight: 600,
                color: "#fff",
                background: completing || loading ? "#9ca3af" : "#166534",
                border: "none",
                borderRadius: "6px",
                cursor: completing || loading ? "not-allowed" : "pointer",
              }}
            >
              {completing ? "Completing…" : "Complete Review"}
            </button>
          </div>

          <p style={{ margin: "12px 0 0", fontSize: "0.72rem", color: "#9ca3af" }}>
            All mandatory requirements must be reviewed and an explicit decision must be selected before completing.
          </p>
        </>
      )}
    </div>
  );
}
