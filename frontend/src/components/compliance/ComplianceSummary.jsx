/**
 * ComplianceSummary — Task 16
 * Displays compliance statistics panel derived from the evaluation summary.
 * Data comes from the server; no frontend recalculation.
 */

import React from "react";

const STAT_COLORS = {
  total: { label: "Total", color: "#374151", bg: "#f9fafb" },
  passed: { label: "Passed", color: "#166534", bg: "#dcfce7" },
  failed: { label: "Failed", color: "#991b1b", bg: "#fee2e2" },
  partial: { label: "Partial", color: "#92400e", bg: "#fef3c7" },
  not_verified: { label: "Not Verified", color: "#7c3aed", bg: "#ede9fe" },
  not_applicable: { label: "N/A", color: "#6b7280", bg: "#f3f4f6" },
};

const REVIEW_STATUS_LABELS = {
  PENDING: { label: "Pending", color: "#6b7280" },
  IN_PROGRESS: { label: "In Progress", color: "#1d4ed8" },
  COMPLETED: { label: "Completed", color: "#166534" },
};

const DECISION_LABELS = {
  QUALIFIED: { label: "Qualified", color: "#166534" },
  NOT_QUALIFIED: { label: "Not Qualified", color: "#991b1b" },
  REQUIRES_CLARIFICATION: { label: "Requires Clarification", color: "#92400e" },
  WITHDRAWN: { label: "Withdrawn", color: "#6b7280" },
  NO_DECISION: { label: "No Decision", color: "#9ca3af" },
};

export default function ComplianceSummary({ summary, review }) {
  if (!summary) return null;

  const stats = [
    { key: "total", value: summary.total },
    { key: "passed", value: summary.passed },
    { key: "failed", value: summary.failed },
    { key: "partial", value: summary.partial },
    { key: "not_verified", value: summary.not_verified },
    { key: "not_applicable", value: summary.not_applicable },
  ];

  const reviewStatus = review?.status || null;
  const decision = review?.decision || "NO_DECISION";
  const rsConf = reviewStatus ? (REVIEW_STATUS_LABELS[reviewStatus] || {}) : null;
  const decConf = DECISION_LABELS[decision] || DECISION_LABELS.NO_DECISION;

  return (
    <div
      style={{
        background: "#fff",
        border: "1px solid #e5e7eb",
        borderRadius: "8px",
        padding: "20px 24px",
        marginBottom: "20px",
      }}
    >
      <h3 style={{ margin: "0 0 16px", fontSize: "1rem", fontWeight: 600, color: "#111827" }}>
        Compliance Assessment
      </h3>

      {/* Stats grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(100px, 1fr))",
          gap: "10px",
          marginBottom: "16px",
        }}
      >
        {stats.map(({ key, value }) => {
          const cfg = STAT_COLORS[key];
          return (
            <div
              key={key}
              style={{
                textAlign: "center",
                padding: "10px 8px",
                borderRadius: "6px",
                background: cfg.bg,
                border: `1px solid ${cfg.color}22`,
              }}
            >
              <div style={{ fontSize: "1.5rem", fontWeight: 700, color: cfg.color }}>{value}</div>
              <div style={{ fontSize: "0.7rem", color: cfg.color, fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                {cfg.label}
              </div>
            </div>
          );
        })}
      </div>

      {/* Review status and decision */}
      {review && (
        <div style={{ borderTop: "1px solid #f3f4f6", paddingTop: "14px", display: "flex", gap: "20px", flexWrap: "wrap", alignItems: "center" }}>
          <div>
            <span style={{ fontSize: "0.75rem", color: "#6b7280", fontWeight: 500 }}>Review Status: </span>
            <span style={{ fontWeight: 600, color: rsConf?.color || "#374151" }}>{rsConf?.label || reviewStatus}</span>
          </div>
          <div>
            <span style={{ fontSize: "0.75rem", color: "#6b7280", fontWeight: 500 }}>Officer Decision: </span>
            <span style={{ fontWeight: 600, color: decConf.color }}>{decConf.label}</span>
          </div>
        </div>
      )}

      {/* Important notice */}
      <p style={{ margin: "12px 0 0", fontSize: "0.75rem", color: "#6b7280", fontStyle: "italic" }}>
        Compliance assessment completed — Officer review required. The system recommends and explains; the Procurement Officer decides.
      </p>
    </div>
  );
}
