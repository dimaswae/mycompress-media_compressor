import React, { useCallback } from "react"

interface UploadDropzoneProps {
  onFileSelect: (file: File) => void
  accept?: string
}

export function UploadDropzone({
  onFileSelect,
  accept = "*",
}: UploadDropzoneProps) {
  const handleDrag = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
    },
    []
  )

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      const file = e.dataTransfer.files[0]
      if (file) onFileSelect(file)
    },
    [onFileSelect]
  )

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (file) onFileSelect(file)
    },
    [onFileSelect]
  )

  return (
    <div
      className="border-2 border-dashed border-gray-600 rounded-lg p-8 text-center cursor-pointer hover:border-gray-500"
      onDragOver={handleDrag}
      onDrop={handleDrop}
      onClick={() => document.getElementById("file-input")?.click()}
    >
      <p className="text-gray-400">Drop files here or click to select</p>
      <input
        id="file-input"
        type="file"
        className="hidden"
        accept={accept}
        onChange={handleChange}
      />
    </div>
  )
}