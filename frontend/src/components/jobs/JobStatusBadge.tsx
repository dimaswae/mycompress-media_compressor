type Status = "pending" | "processing" | "done" | "failed" | "deleted" | "running"

interface JobStatusBadgeProps {
  status: Status
}

const DOT_COLOR: Record<string, string> = {
  done:       "#4ade80",
  pending:    "#fbbf24",
  processing: "#38bdf8",
  running:    "#38bdf8",
  failed:     "#f87171",
  deleted:    "#64748b",
}

const BADGE_CLASS: Record<string, string> = {
  done:       "badge badge-done",
  pending:    "badge badge-pending",
  processing: "badge badge-running",
  running:    "badge badge-running",
  failed:     "badge badge-failed",
  deleted:    "badge",
}

export function JobStatusBadge({ status }: JobStatusBadgeProps) {
  const cls = BADGE_CLASS[status] ?? "badge"
  const dotColor = DOT_COLOR[status] ?? "var(--color-muted)"
  return (
    <span className={cls}>
      <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: dotColor, display: "inline-block", flexShrink: 0 }} />
      {status}
    </span>
  )
}