import React, { useState } from "react"

interface EncryptionToggleProps {
  onPasswordChange: (password: string) => void
  isEnabled: boolean
  onToggle: (enabled: boolean) => void
}

export function EncryptionToggle({
  onPasswordChange,
  isEnabled,
  onToggle,
}: EncryptionToggleProps) {
  const [password, setPassword] = useState("")
  const [showPw, setShowPw] = useState(false)

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value
    setPassword(val)
    onPasswordChange(val)
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
      {/* Toggle row */}
      <label style={{ display: "flex", alignItems: "center", gap: "0.75rem", cursor: "pointer" }}>
        {/* Custom toggle */}
        <div
          onClick={() => onToggle(!isEnabled)}
          style={{
            width: "2.25rem", height: "1.25rem",
            borderRadius: "999px",
            background: isEnabled ? "var(--color-primary)" : "var(--color-surface-2)",
            border: `1px solid ${isEnabled ? "var(--color-primary)" : "var(--color-border)"}`,
            position: "relative", flexShrink: 0,
            transition: "all 200ms ease",
            cursor: "pointer",
          }}
          role="switch"
          aria-checked={isEnabled}
          tabIndex={0}
          onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onToggle(!isEnabled) }}}
        >
          <div style={{
            position: "absolute", top: "2px",
            left: isEnabled ? "calc(100% - 1rem - 2px)" : "2px",
            width: "1rem", height: "1rem",
            borderRadius: "50%",
            background: isEnabled ? "#0F172A" : "var(--color-muted-2)",
            transition: "left 200ms ease",
          }} />
        </div>
        <div>
          <span style={{ fontWeight: 600, color: "var(--color-text)", fontSize: "0.9375rem" }}>AES-256 Encryption</span>
          <span style={{ color: "var(--color-muted)", fontSize: "0.8125rem", display: "block" }}>
            Encrypt the hidden message with a password
          </span>
        </div>
      </label>

      {/* Password input */}
      {isEnabled && (
        <div style={{ position: "relative" }}>
          <input
            type={showPw ? "text" : "password"}
            className="input"
            value={password}
            onChange={handlePasswordChange}
            placeholder="Enter encryption password"
            style={{ paddingRight: "2.75rem" }}
            aria-label="Encryption password"
          />
          <button
            type="button"
            onClick={() => setShowPw(!showPw)}
            style={{
              position: "absolute", right: "0.75rem", top: "50%", transform: "translateY(-50%)",
              background: "none", border: "none", cursor: "pointer",
              color: "var(--color-muted)", padding: 0, lineHeight: 0,
            }}
            aria-label={showPw ? "Hide password" : "Show password"}
          >
            {showPw
              ? <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" /><line x1="1" y1="1" x2="23" y2="23" /></svg>
              : <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" /></svg>
            }
          </button>
        </div>
      )}
    </div>
  )
}