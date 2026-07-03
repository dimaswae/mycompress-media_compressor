import React from "react"

interface AudioCompareViewProps {
  originalUrl: string
  resultUrl: string
}

export function AudioCompareView({
  originalUrl,
  resultUrl,
}: AudioCompareViewProps) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col">
        <span className="text-sm text-gray-400 mb-2">Original</span>
        <audio controls src={originalUrl} className="w-full" />
      </div>
      <div className="flex flex-col">
        <span className="text-sm text-gray-400 mb-2">Result</span>
        <audio controls src={resultUrl} className="w-full" />
      </div>
    </div>
  )
}