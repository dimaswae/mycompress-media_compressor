interface ImageCompareViewProps {
  originalUrl: string
  resultUrl: string
}

export function ImageCompareView({
  originalUrl,
  resultUrl,
}: ImageCompareViewProps) {
  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="flex flex-col">
        <span className="text-sm text-gray-400 mb-2">Original</span>
        <img src={originalUrl} alt="Original" className="max-w-full rounded" />
      </div>
      <div className="flex flex-col">
        <span className="text-sm text-gray-400 mb-2">Result</span>
        <img src={resultUrl} alt="Result" className="max-w-full rounded" />
      </div>
    </div>
  )
}