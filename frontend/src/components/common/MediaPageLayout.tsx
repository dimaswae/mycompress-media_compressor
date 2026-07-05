import { Link } from "react-router-dom"

interface MediaPageLayoutProps {
  title: string
  subtitle: string
  icon: React.ReactNode
  accentColor: string
  backTo?: string
  children: React.ReactNode
}

export function MediaPageLayout({
  title,
  subtitle,
  icon,
  accentColor,
  children,
}: MediaPageLayoutProps) {
  return (
    <div style={{ padding: "2rem 1.5rem 4rem" }}>
      <div className="container-md">
        {/* Page header */}
        <div style={{ marginBottom: "2rem" }}>
          <Link
            to="/"
            style={{
              display: "inline-flex", alignItems: "center", gap: "0.375rem",
              color: "var(--color-muted)", fontSize: "0.875rem", fontWeight: 500,
              textDecoration: "none", marginBottom: "1.25rem",
              transition: "color 200ms",
            }}
            onMouseEnter={(e) => { (e.currentTarget as HTMLAnchorElement).style.color = "var(--color-text)" }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLAnchorElement).style.color = "var(--color-muted)" }}
          >
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M19 12H5M12 5l-7 7 7 7" /></svg>
            Back to Home
          </Link>

          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <div style={{
              width: "3rem", height: "3rem",
              background: `${accentColor}1a`, border: `1px solid ${accentColor}33`,
              borderRadius: "0.875rem", display: "flex", alignItems: "center",
              justifyContent: "center", color: accentColor, flexShrink: 0,
            }}>
              {icon}
            </div>
            <div>
              <h1 style={{ fontSize: "1.625rem", fontWeight: 800, marginBottom: "0.25rem" }}>{title}</h1>
              <p style={{ color: "var(--color-muted)", fontSize: "0.9rem", margin: 0 }}>{subtitle}</p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          {children}
        </div>
      </div>
    </div>
  )
}

/* ── Section Card ─────────────────────────────────────────────── */
export function Section({ title, children }: { title?: string; children: React.ReactNode }) {
  return (
    <div className="card" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
      {title && (
        <h2 style={{ fontSize: "0.9375rem", fontWeight: 700, color: "var(--color-muted)", textTransform: "uppercase", letterSpacing: "0.06em", margin: 0 }}>
          {title}
        </h2>
      )}
      {children}
    </div>
  )
}

/* ── Job Status Panel ─────────────────────────────────────────── */
export function JobStatusPanel({ status, jobId }: { status: string; jobId?: string }) {
  const isRunning = status === "processing" || status === "running" || status === "pending"
  const isDone = status === "done"

  return (
    <div style={{
      display: "flex", alignItems: "center", gap: "0.875rem",
      padding: "0.875rem 1rem",
      background: isDone ? "rgba(34,197,94,0.06)" : isRunning ? "rgba(56,189,248,0.06)" : "rgba(248,113,113,0.06)",
      border: `1px solid ${isDone ? "rgba(34,197,94,0.2)" : isRunning ? "rgba(56,189,248,0.2)" : "rgba(248,113,113,0.2)"}`,
      borderRadius: "var(--radius-sm)",
    }}>
      {isRunning && <span className="spinner" style={{ borderTopColor: "#38bdf8", borderColor: "rgba(56,189,248,0.2)" }} />}
      {isDone && (
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#4ade80" strokeWidth="2.5"><path d="M20 6L9 17l-5-5" /></svg>
      )}
      <div style={{ flex: 1 }}>
        <span style={{ fontWeight: 600, fontSize: "0.9375rem", color: "var(--color-text)", textTransform: "capitalize" }}>
          {status}
        </span>
        {jobId && (
          <span style={{ color: "var(--color-muted)", fontSize: "0.8125rem", marginLeft: "0.5rem", fontFamily: "ui-monospace, monospace" }}>
            #{jobId.slice(0, 8)}
          </span>
        )}
      </div>
    </div>
  )
}

/* ── Result Panel ─────────────────────────────────────────────── */
function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B"
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

interface ResultPanelProps {
  jobId: string
  /** Original file size in bytes (from compare API response). Optional — hide size row if absent. */
  originalSize?: number
  /** Result file size in bytes. Optional — hide size row if absent. */
  resultSize?: number
  /** Extra children rendered below the size summary (e.g. image compare view). */
  children?: React.ReactNode
  /** Flat metrics object rendered in the collapsible detail section. */
  metrics?: Record<string, number>
  accentColor?: string
}

export function ResultPanel({
  jobId,
  originalSize,
  resultSize,
  children,
  metrics,
  accentColor = "var(--color-primary)",
}: ResultPanelProps) {
  const apiBase = (import.meta.env.VITE_API_BASE as string | undefined) ?? "/api/v1"
  const downloadUrl = `${apiBase}/jobs/${jobId}/download`

  const showSizeSummary =
    typeof originalSize === "number" && typeof resultSize === "number" && originalSize > 0

  let deltaPercent: number | null = null
  if (showSizeSummary && originalSize! > 0) {
    deltaPercent = ((resultSize! - originalSize!) / originalSize!) * 100
  }

  return (
    <div className="card" style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
      {/* ── 1. Download button ── */}
      <a
        id={`download-btn-${jobId}`}
        href={downloadUrl}
        download
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "0.625rem",
          padding: "0.875rem 1.5rem",
          background: `linear-gradient(135deg, ${accentColor}, ${accentColor}cc)`,
          color: "#0f172a",
          fontWeight: 700,
          fontSize: "1rem",
          borderRadius: "var(--radius-sm)",
          textDecoration: "none",
          boxShadow: `0 4px 16px ${accentColor}40`,
          transition: "opacity 150ms, transform 150ms",
        }}
        onMouseEnter={(e) => {
          (e.currentTarget as HTMLAnchorElement).style.opacity = "0.9"
          ;(e.currentTarget as HTMLAnchorElement).style.transform = "translateY(-1px)"
        }}
        onMouseLeave={(e) => {
          (e.currentTarget as HTMLAnchorElement).style.opacity = "1"
          ;(e.currentTarget as HTMLAnchorElement).style.transform = "translateY(0)"
        }}
      >
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="7 10 12 15 17 10" />
          <line x1="12" y1="15" x2="12" y2="3" />
        </svg>
        Download Result
      </a>

      {/* ── 2. Size summary ── */}
      {showSizeSummary && (
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: "0.75rem",
          padding: "0.75rem 1rem",
          background: "var(--color-surface-2)",
          borderRadius: "var(--radius-sm)",
          flexWrap: "wrap",
        }}>
          <span style={{ color: "var(--color-muted)", fontSize: "0.875rem" }}>
            {formatBytes(originalSize!)}
          </span>
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="var(--color-muted)" strokeWidth="2"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
          <span style={{ fontWeight: 700, color: "var(--color-text)", fontSize: "0.9375rem" }}>
            {formatBytes(resultSize!)}
          </span>
          {deltaPercent !== null && (
            <span style={{
              marginLeft: "auto",
              fontWeight: 700,
              fontSize: "0.9375rem",
              color: deltaPercent < 0 ? "#4ade80" : deltaPercent === 0 ? "var(--color-muted)" : "#f87171",
            }}>
              {deltaPercent < 0
                ? `▼ ${Math.abs(deltaPercent).toFixed(1)}%`
                : deltaPercent === 0
                ? "±0%"
                : `▲ ${deltaPercent.toFixed(1)}%`}
            </span>
          )}
        </div>
      )}

      {/* ── 3. Extra content slot (e.g. image compare view) ── */}
      {children}

      {/* ── 4. Collapsible technical metrics ── */}
      {metrics && Object.keys(metrics).length > 0 && (
        <details style={{ borderTop: "1px solid var(--color-border)", paddingTop: "0.75rem" }}>
          <summary style={{
            cursor: "pointer",
            fontSize: "0.8125rem",
            fontWeight: 600,
            color: "var(--color-muted)",
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            userSelect: "none",
            listStyle: "none",
            display: "flex",
            alignItems: "center",
            gap: "0.375rem",
          }}>
            <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M6 9l6 6 6-6" /></svg>
            Technical details
          </summary>
          <div style={{ marginTop: "0.75rem", display: "flex", flexDirection: "column", gap: "0.375rem" }}>
            {Object.entries(metrics).map(([key, val]) => (
              <div key={key} style={{
                display: "flex",
                justifyContent: "space-between",
                fontSize: "0.875rem",
                padding: "0.25rem 0",
                borderBottom: "1px solid var(--color-border)",
              }}>
                <span style={{ color: "var(--color-muted)", fontFamily: "ui-monospace, monospace" }}>{key}</span>
                <span style={{ fontWeight: 600, color: "var(--color-text)", fontFamily: "ui-monospace, monospace" }}>
                  {typeof val === "number" ? val.toFixed(4) : val}
                </span>
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  )
}
