import React from "react"

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

  return (
    <div
      className={`text-sm ${isExceeding ? "text-red-400" : "text-gray-400"}`}
    >
      Message capacity: {capacityBytes} bytes
      {isExceeding && " (Warning: message may exceed capacity)"}
    </div>
  )
}