/**
 * ReviewStatusBadge — Task 16
 * Displays requirement-level review status: NOT_REVIEWED | REVIEWED | FLAGGED
 */

import React from "react";

const STATUS_CONFIG = {
  NOT_REVIEWED: { label: "Not Reviewed", color: "#6b7280", bg: "#f3f4f6" },
  REVIEWED: { label: "Reviewed", color: "#166534", bg: "#dcfce7" },
  FLAGGED: { label: "Flagged", color: "#92400e", bg: "#fef3c7" },
};

export default function ReviewStatusBadge({ status }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.NOT_REVIEWED;
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "4px",
        padding: "2px 10px",
        borderRadius: "12px",
        fontSize: "0.75rem",
        fontWeight: 600,
        letterSpacing: "0.04em",
        color: cfg.color,
        background: cfg.bg,
        border: `1px solid ${cfg.color}33`,
      }}
    >
      {status === "REVIEWED" && "✓ "}
      {status === "FLAGGED" && "⚑ "}
      {cfg.label}
    </span>
  );
}
