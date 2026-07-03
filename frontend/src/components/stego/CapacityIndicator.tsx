import React from "react"

interface CapacityIndicatorProps {
  messageLength: number
  capacityBits: number
}

export function CapacityIndicator({
  messageLength,
  capacityBits,
}: CapacityIndicatorProps) {
  const capacityBytes = Math.floor(capacityBits / 8) - 4 // -4 for length prefix
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