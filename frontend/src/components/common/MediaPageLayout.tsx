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
