import { useEffect, useState } from "react"
import { UploadDropzone } from "../components/upload/UploadDropzoneNew"
import { Button } from "../components/common/Button"
import { MessageInput } from "../components/stego/MessageInput"
import { EncryptionToggle } from "../components/stego/EncryptionToggle"
import { CapacityIndicator } from "../components/stego/CapacityIndicator"
import { MediaPageLayout, Section, JobStatusPanel, ResultPanel } from "../components/common/MediaPageLayout"
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

function IconImage() {
  return (
    <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <circle cx="8.5" cy="8.5" r="1.5" />
      <polyline points="21 15 16 10 5 21" />
    </svg>
  )
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
      showToast("Job started successfully", "info")
    }
  }

  const handleFileSelect = (file: File) => {
    setSelectedFile(file)
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
  }

  return (
    <MediaPageLayout
      title="Image Processing"
      subtitle="Compress, embed, and extract hidden messages in PNG/JPEG"
      icon={<IconImage />}
      accentColor="#22c55e"
    >
      {/* Upload */}
      <Section title="1. Select File">
        <UploadDropzone
          onFileSelect={handleFileSelect}
          accept="image/*"
          selectedFileName={selectedFile?.name}
        />
      </Section>

      {/* Steganography config */}
      <Section title="2. Steganography Settings">
        <MessageInput value={message} onChange={setMessage} />
        <EncryptionToggle
          isEnabled={encryptEnabled}
          onToggle={setEncryptEnabled}
          onPasswordChange={setPassword}
        />
        {capacity > 0 && (
          <CapacityIndicator
            messageLength={message.length}
            capacityBits={capacity}
            isEncryptionEnabled={encryptEnabled}
          />
        )}
      </Section>

      {/* Compression algorithm */}
      <Section title="3. Compression Algorithm">
        <div style={{ display: "flex", gap: "0.75rem" }}>
          {["rle", "huffman"].map((opt) => (
            <label
              key={opt}
              style={{
                display: "flex", alignItems: "center", gap: "0.5rem",
                cursor: "pointer", padding: "0.5rem 1rem",
                background: algo === opt ? "rgba(34,197,94,0.1)" : "var(--color-surface-2)",
                border: `1px solid ${algo === opt ? "rgba(34,197,94,0.4)" : "var(--color-border)"}`,
                borderRadius: "var(--radius-sm)",
                transition: "all 200ms",
                color: algo === opt ? "var(--color-primary)" : "var(--color-muted)",
                fontWeight: algo === opt ? 600 : 500,
                fontSize: "0.9375rem",
              }}
            >
              <input
                type="radio"
                name="algo"
                value={opt}
                checked={algo === opt}
                onChange={() => setAlgo(opt)}
                style={{ display: "none" }}
              />
              {opt.toUpperCase()}
            </label>
          ))}
        </div>
      </Section>

      {/* Submit */}
      <Button onClick={handleUpload} disabled={!selectedFile || isUploading} isLoading={isUploading}>
        Embed Message
      </Button>

      {/* Errors */}
      {(uploadError || pollingError) && (
        <ErrorBanner message={uploadError || pollingError || "Unknown error"} />
      )}

      {/* Upload progress */}
      {(isUploading || progress > 0) && <UploadProgress percent={progress} />}

      {/* Job status */}
      {status && !job?.job_id && (
        <JobStatusPanel status={status} />
      )}

      {/* Result panel — shown once job_id is known */}
      {status === "done" && job?.job_id && (
        <ResultPanel
          jobId={job.job_id}
          originalSize={compareData?.original_size}
          resultSize={compareData?.result_size}
          metrics={compareData?.metrics}
          accentColor="#22c55e"
        >
          {compareData && (
            <ImageCompareView
              originalUrl={getAbsoluteUrl(compareData.original_url)}
              resultUrl={getAbsoluteUrl(compareData.result_url)}
            />
          )}
        </ResultPanel>
      )}

      {/* In-progress status banner */}
      {status && status !== "done" && job?.job_id && (
        <JobStatusPanel status={status} jobId={job.job_id} />
      )}
    </MediaPageLayout>
  )
}