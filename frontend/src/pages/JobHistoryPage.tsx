import { useEffect, useState } from "react"
import { JobStatusBadge } from "../components/jobs/JobStatusBadge"
import * as jobsApi from "../api/jobsApi"
import type { JobStatusResponse } from "../types/job"

function formatDate(iso: string | undefined | null) {
  if (!iso) return "—"
  try {
    return new Intl.DateTimeFormat("id-ID", { dateStyle: "medium", timeStyle: "short" }).format(new Date(iso))
  } catch {
    return iso
  }
}

const MEDIA_COLORS: Record<string, string> = {
  image: "#22c55e",
  audio: "#38bdf8",
  video: "#a78bfa",
}

export function JobHistoryPage() {
  const [jobs, setJobs] = useState<JobStatusResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    jobsApi.listJobs()
      .then(setJobs)
      .catch((e) => setError(e.message ?? "Failed to load jobs"))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div style={{ padding: "2rem 1.5rem 4rem" }}>
      <div className="container-lg">
        {/* Header */}
        <div style={{ marginBottom: "2rem" }}>
          <h1 style={{ fontSize: "1.75rem", fontWeight: 800, marginBottom: "0.375rem" }}>Job History</h1>
          <p style={{ color: "var(--color-muted)", margin: 0, fontSize: "0.9375rem" }}>
            All compression and steganography jobs processed on this instance
          </p>
        </div>

        {/* States */}
        {loading && (
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", color: "var(--color-muted)", padding: "3rem 0" }}>
            <span className="spinner" />
            Loading jobs...
          </div>
        )}

        {error && (
          <div style={{
            display: "flex", gap: "0.75rem", alignItems: "flex-start",
            background: "rgba(248,113,113,0.08)", border: "1px solid rgba(248,113,113,0.25)",
            borderRadius: "var(--radius-sm)", padding: "1rem", color: "var(--color-error)",
          }}>
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" /></svg>
            {error}
          </div>
        )}

        {!loading && !error && jobs.length === 0 && (
          <div style={{ textAlign: "center", padding: "4rem 0", color: "var(--color-muted)" }}>
            <svg viewBox="0 0 24 24" width="40" height="40" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ margin: "0 auto 1rem", display: "block", opacity: 0.4 }}><rect x="2" y="7" width="20" height="14" rx="2" /><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2" /></svg>
            <p style={{ margin: 0, fontWeight: 600, fontSize: "1.0625rem", marginBottom: "0.25rem" }}>No jobs yet</p>
            <p style={{ margin: 0, fontSize: "0.9rem" }}>Upload a file on the Image, Audio, or Video page to get started.</p>
          </div>
        )}

        {!loading && !error && jobs.length > 0 && (
          <div style={{
            background: "var(--color-surface)", border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-lg)", overflow: "hidden",
          }}>
            {/* Table header */}
            <div style={{
              display: "grid",
              gridTemplateColumns: "2fr 1fr 1.25fr 1fr",
              padding: "0.625rem 1.25rem",
              background: "var(--color-surface-2)",
              borderBottom: "1px solid var(--color-border)",
            }}>
              {["Job ID", "Type", "Operation", "Status"].map((h) => (
                <span key={h} style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--color-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
                  {h}
                </span>
              ))}
            </div>

            {/* Rows */}
            {jobs.map((job, idx) => {
              const accentColor = MEDIA_COLORS[job.media_type ?? ""] ?? "var(--color-muted)"
              return (
                <div
                  key={job.job_id}
                  style={{
                    display: "grid",
                    gridTemplateColumns: "2fr 1fr 1.25fr 1fr",
                    padding: "0.875rem 1.25rem",
                    borderBottom: idx < jobs.length - 1 ? "1px solid var(--color-border)" : "none",
                    transition: "background 150ms",
                    alignItems: "center",
                  }}
                  onMouseEnter={(e) => { (e.currentTarget as HTMLDivElement).style.background = "var(--color-surface-2)" }}
                  onMouseLeave={(e) => { (e.currentTarget as HTMLDivElement).style.background = "transparent" }}
                >
                  {/* Job ID */}
                  <div>
                    <span style={{ fontFamily: "ui-monospace, monospace", fontSize: "0.875rem", color: "var(--color-text)" }} title={job.job_id}>
                      {job.job_id.slice(0, 8)}...
                    </span>
                    {(job as any).created_at && (
                      <div style={{ fontSize: "0.75rem", color: "var(--color-muted-2)", marginTop: "0.125rem" }}>
                        {formatDate((job as any).created_at)}
                      </div>
                    )}
                  </div>

                  {/* Media type */}
                  <div>
                    {job.media_type ? (
                      <span style={{
                        fontSize: "0.8125rem", fontWeight: 600,
                        color: accentColor,
                        background: `${accentColor}18`,
                        border: `1px solid ${accentColor}30`,
                        padding: "0.2rem 0.625rem", borderRadius: "999px",
                      }}>
                        {job.media_type}
                      </span>
                    ) : (
                      <span style={{ color: "var(--color-muted-2)" }}>—</span>
                    )}
                  </div>

                  {/* Operation */}
                  <div style={{ color: "var(--color-muted)", fontSize: "0.9rem", textTransform: "capitalize" }}>
                    {job.operation ?? "—"}
                  </div>

                  {/* Status */}
                  <div>
                    <JobStatusBadge status={job.status as any} />
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* Summary */}
        {!loading && !error && jobs.length > 0 && (
          <p style={{ color: "var(--color-muted-2)", fontSize: "0.8125rem", marginTop: "0.875rem", textAlign: "right" }}>
            {jobs.length} job{jobs.length !== 1 ? "s" : ""} total
          </p>
        )}
      </div>
    </div>
  )
}