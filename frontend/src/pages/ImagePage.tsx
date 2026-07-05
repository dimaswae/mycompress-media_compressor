import { useEffect, useState } from "react"
import { UploadDropzone } from "../components/upload/UploadDropzoneNew"
import { Button } from "../components/common/Button"
import { MessageInput } from "../components/stego/MessageInput"
import { EncryptionToggle } from "../components/stego/EncryptionToggle"
import { CapacityIndicator } from "../components/stego/CapacityIndicator"
import { useFileUpload } from "../hooks/useFileUpload"
import { useJobPolling } from "../hooks/useJobPolling"
import * as imageApi from "../api/imageApi"
import { ErrorBanner } from "../components/common/ErrorBanner"
import { UploadProgress } from "../components/upload/UploadProgressNew"
import { useToast } from "../components/common/ToastContext"
import { ImageCompareView } from "../components/comparison/ImageCompareView"
import { MetricsTable } from "../components/metrics/MetricsTable"
import type { CompareResponse } from "../types/media"

const getAbsoluteUrl = (path: string | undefined | null) => {
  if (!path) return ""
  const base = import.meta.env.VITE_API_BASE || "/api/v1"
  if (base.endsWith("/api/v1") && path.startsWith("/api/v1")) {
    return `${base}${path.substring(7)}`
  }
  return `${base}${path}`
}

export function ImagePage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [message, setMessage] = useState("")
  const [password, setPassword] = useState("")
  const [encryptEnabled, setEncryptEnabled] = useState(false)
  const [algo, setAlgo] = useState("rle")
  const [jobId, setJobId] = useState<string | null>(null)
  const [capacity, setCapacity] = useState(0)
  const [compareData, setCompareData] = useState<CompareResponse | null>(null)

  const { upload, progress, isUploading, error: uploadError } = useFileUpload()
  const { status, job, error: pollingError } = useJobPolling(jobId || "")
  const { showToast } = useToast()

  useEffect(() => {
    if (status === "done" && jobId) {
      imageApi.compareImage(jobId)
        .then(setCompareData)
        .catch((e) => showToast(`Failed to fetch comparison: ${e.message}`, "error"))
    } else {
      setCompareData(null)
    }
  }, [status, jobId, showToast])

  const handleUpload = async () => {
    if (!selectedFile) return
    const result = await upload(() =>
      imageApi.embedMessage(selectedFile, message, encryptEnabled ? password : undefined, algo || undefined)
    )
    if (result?.job_id) {
      setJobId(result.job_id)
      showToast("Upload started", "info")
    }
  }

  const handleFileSelect = (file: File) => {
    setSelectedFile(file)
    // Estimate capacity based on actual image dimensions (width * height * 3 channels)
    const img = new globalThis.Image()
    img.src = URL.createObjectURL(file)
    img.onload = () => {
      setCapacity(img.width * img.height * 3)
      URL.revokeObjectURL(img.src)
    }
    img.onerror = () => {
      setCapacity(0)
      URL.revokeObjectURL(img.src)
    }
    showToast(`Selected file: ${file.name}`, "info")
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-4">Image Processing</h1>

      <div className="space-y-4">
        <UploadDropzone onFileSelect={handleFileSelect} accept="image/*" />

        <MessageInput value={message} onChange={setMessage} />

        <EncryptionToggle
          isEnabled={encryptEnabled}
          onToggle={setEncryptEnabled}
          onPasswordChange={setPassword}
        />

        <CapacityIndicator messageLength={message.length} capacityBits={capacity} isEncryptionEnabled={encryptEnabled} />

        <select
          className="bg-gray-800 border border-gray-600 rounded p-2 text-white"
          value={algo}
          onChange={(e) => setAlgo(e.target.value)}
        >
          <option value="rle">RLE</option>
          <option value="huffman">Huffman</option>
        </select>

        <Button onClick={handleUpload} disabled={!selectedFile || isUploading} isLoading={isUploading}>
          Embed Message
        </Button>

        {(uploadError || pollingError) && <ErrorBanner message={uploadError || pollingError || "Unknown error"} />}

        {(isUploading || progress > 0) && (
          <div className="mt-2">
            <UploadProgress percent={progress} />
          </div>
        )}

        {status && (
          <div className="mt-4 p-4 bg-gray-800 rounded space-y-4">
            <p className="text-white">Job Status: {status}</p>
            {job && <p className="text-gray-400">Job ID: {job.job_id}</p>}

            {status === "done" && compareData && (
              <div className="mt-4 space-y-6">
                <div className="border-t border-gray-700 pt-4">
                  <h3 className="text-lg font-semibold text-white mb-3">Comparison</h3>
                  <ImageCompareView
                    originalUrl={getAbsoluteUrl(compareData.original_url)}
                    resultUrl={getAbsoluteUrl(compareData.result_url)}
                  />
                </div>
                <div className="border-t border-gray-700 pt-4">
                  <h3 className="text-lg font-semibold text-white mb-3">Metrics</h3>
                  <MetricsTable metrics={compareData.metrics} />
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}