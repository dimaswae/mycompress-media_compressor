import React from "react"

interface UploadProgressProps {
  percent: number
}

export function UploadProgress({ percent }: UploadProgressProps) {
  return (
    <div className="w-full bg-gray-700 rounded-full h-4">
      <div
        className="bg-blue-600 h-4 rounded-full transition-all"
        style={{ width: `${percent}%` }}
      />
    </div>
  )
}