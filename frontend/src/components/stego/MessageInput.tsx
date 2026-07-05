interface MessageInputProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  label?: string
  maxLength?: number
}

export function MessageInput({
  value,
  onChange,
  placeholder = "Enter secret message...",
  label = "Hidden Message",
  maxLength = 1000,
}: MessageInputProps) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.375rem" }}>
      <label style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--color-muted)" }}>
        {label}
      </label>
      <textarea
        className="input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={4}
        maxLength={maxLength}
        style={{ resize: "vertical", minHeight: "5rem", fontFamily: "var(--font-sans)" }}
        aria-label={label}
      />
      <span style={{ fontSize: "0.75rem", color: "var(--color-muted-2)", alignSelf: "flex-end" }}>
        {value.length} / {maxLength} chars
      </span>
    </div>
  )
}