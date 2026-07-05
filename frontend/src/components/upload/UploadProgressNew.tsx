interface UploadProgressProps {
  percent: number
}

export function UploadProgress({ percent }: UploadProgressProps) {
  const pct = Math.max(0, Math.min(100, Math.round(percent)))
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.375rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: "0.8125rem", color: "var(--color-muted)", fontWeight: 500 }}>Uploading...</span>
        <span style={{ fontSize: "0.8125rem", color: "var(--color-primary)", fontWeight: 700 }}>{pct}%</span>
      </div>
      <div
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={pct}
        className="progress-track"
      >
        <div className="progress-bar" style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}
