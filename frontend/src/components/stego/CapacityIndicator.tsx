interface CapacityIndicatorProps {
  messageLength: number
  capacityBits: number
  isEncryptionEnabled?: boolean
}

export function CapacityIndicator({
  messageLength,
  capacityBits,
  isEncryptionEnabled = false,
}: CapacityIndicatorProps) {
  const capacityBytes = Math.max(0, Math.floor(capacityBits / 8) - 4 - (isEncryptionEnabled ? 44 : 0))
  const isExceeding = messageLength > capacityBytes
  const usedPct = capacityBytes > 0 ? Math.min(100, (messageLength / capacityBytes) * 100) : 0

  if (capacityBytes === 0) return null

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.375rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: "0.8125rem", color: "var(--color-muted)", fontWeight: 500 }}>
          Message capacity: {capacityBytes} bytes
        </span>
        {isExceeding && (
          <span style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--color-error)" }}>
            (Warning: message may exceed capacity)
          </span>
        )}
      </div>
      <div className="progress-track">
        <div
          className="progress-bar"
          style={{
            width: `${usedPct}%`,
            background: isExceeding
              ? "var(--color-error)"
              : usedPct > 75
                ? "linear-gradient(90deg,var(--color-warn),#f97316)"
                : undefined,
          }}
        />
      </div>
    </div>
  )
}