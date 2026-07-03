import React from "react"

interface VideoCompareViewProps {
  originalUrl: string
  resultUrl: string
}

export function VideoCompareView({
  originalUrl,
  resultUrl,
}: VideoCompareViewProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="flex flex-col">
        <span className="text-sm text-gray-400 mb-2">Original</span>
        <video controls src={originalUrl} className="max-w-full rounded" />
      </div>
      <div className="flex flex-col">
        <span className="text-sm text-gray-400 mb-2">Result</span>
        <video controls src={resultUrl} className="max-w-full rounded" />
      </div>
    </div>
  )
}