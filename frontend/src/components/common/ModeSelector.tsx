/** Shared two-tab mode selector used by Image, Audio, and Video pages. */

export type PageMode = "compress" | "stego"

interface ModeSelectorProps {
  mode: PageMode
  onChange: (m: PageMode) => void
  accentColor: string
  compressLabel?: string
  stegoLabel?: string
}

export function ModeSelector({
  mode,
  onChange,
  accentColor,
  compressLabel = "Compress / Decompress",
  stegoLabel = "Hide / Extract Message",
}: ModeSelectorProps) {
  const tab = (id: PageMode, label: string, icon: React.ReactNode) => {
    const active = mode === id
    return (
      <button
        key={id}
        id={`mode-tab-${id}`}
        role="tab"
        aria-selected={active}
        onClick={() => onChange(id)}
        style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "0.5rem",
          padding: "0.625rem 1rem",
          border: "none",
          borderRadius: "calc(var(--radius-sm) - 2px)",
          cursor: "pointer",
          fontWeight: active ? 700 : 500,
          fontSize: "0.9375rem",
          transition: "all 180ms",
          background: active
            ? `linear-gradient(135deg, ${accentColor}22, ${accentColor}11)`
            : "transparent",
          color: active ? accentColor : "var(--color-muted)",
          boxShadow: active ? `inset 0 0 0 1.5px ${accentColor}55` : "none",
        }}
      >
        {icon}
        {label}
      </button>
    )
  }

  return (
    <div
      role="tablist"
      aria-label="Operation mode"
      style={{
        display: "flex",
        gap: "0.25rem",
        padding: "0.25rem",
        background: "var(--color-surface-2)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-sm)",
      }}
    >
      {tab(
        "compress",
        compressLabel,
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="4 14 10 14 10 20" /><polyline points="20 10 14 10 14 4" />
          <line x1="14" y1="10" x2="21" y2="3" /><line x1="3" y1="21" x2="10" y2="14" />
        </svg>,
      )}
      {tab(
        "stego",
        stegoLabel,
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
          <path d="M7 11V7a5 5 0 0 1 10 0v4" />
        </svg>,
      )}
    </div>
  )
}

/* ── Error message friendly mapper ───────────────────────────── */

/**
 * Maps raw backend error messages / codes to user-friendly strings.
 * Pass in the error.message from a caught ApiError.
 */
export function friendlyError(raw: string | undefined | null, mediaType: "image" | "audio" | "video"): string {
  if (!raw) return "An unexpected error occurred. Please try again."
  const r = raw.toLowerCase()

  // Format / extension errors
  if (r.includes("unsupported extension") || r.includes(".cmp")) {
    const fmts: Record<string, string> = {
      image: "PNG or JPG",
      audio: "WAV",
      video: "MP4",
    }
    return `This file format is not supported for this operation. Please upload an original ${fmts[mediaType]} file.`
  }
  if (r.includes("only wav files are supported")) {
    return "To hide a secret message in audio, please upload an original WAV file (not MP3)."
  }
  if (r.includes("file content does not match") || r.includes("magic")) {
    return "The file content doesn't match its extension. Please upload a valid, unmodified file."
  }

  // Size / capacity errors
  if (r.includes("capacity") || r.includes("exceeds maximum")) {
    return "The message is too long to fit in this file. Try a shorter message or a larger file."
  }
  if (r.includes("file size") && r.includes("exceeds")) {
    return "The file is too large. Please upload a smaller file (max 50 MB)."
  }

  // Auth / encryption errors
  if (r.includes("password") || r.includes("decrypt")) {
    return "Incorrect password or the message is not encrypted. Check your password and try again."
  }
  if (r.includes("encrypted") && r.includes("required")) {
    return "This message was encrypted — a password is required to extract it."
  }

  // Network / generic
  if (r.includes("network error")) {
    return "Network error. Please check your connection and try again."
  }

  // Fallback: show raw but cap length
  return raw.length > 120 ? raw.slice(0, 120) + "…" : raw
}
