import { useState } from "react"
import { UploadDropzone } from "../components/upload/UploadDropzoneNew"
import { Button } from "../components/common/Button"
import { MessageInput } from "../components/stego/MessageInput"
import { EncryptionToggle } from "../components/stego/EncryptionToggle"
import { MediaPageLayout, Section, JobStatusPanel, ResultPanel } from "../components/common/MediaPageLayout"
import { useFileUpload } from "../hooks/useFileUpload"
import { useJobPolling } from "../hooks/useJobPolling"
import * as videoApi from "../api/videoApi"
import { ErrorBanner } from "../components/common/ErrorBanner"
import { UploadProgress } from "../components/upload/UploadProgressNew"
import { useToast } from "../components/common/ToastContext"

function IconVideo() {
  return (
    <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="23 7 16 12 23 17 23 7" />
      <rect x="1" y="5" width="15" height="14" rx="2" />
    </svg>
  )
}

export function VideoPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [message, setMessage] = useState("")
  const [password, setPassword] = useState("")
  const [encryptEnabled, setEncryptEnabled] = useState(false)
  const [crf, setCrf] = useState(28)
  const [jobId, setJobId] = useState<string | null>(null)

  const { upload, progress, isUploading, error: uploadError } = useFileUpload()
  const { status, job, error: pollingError } = useJobPolling(jobId || "")
  const { showToast } = useToast()

  const handleUpload = async () => {
    if (!selectedFile) return
    const result = await upload((onProgress) =>
      videoApi.embedMessage(selectedFile, message, encryptEnabled ? password : undefined, onProgress)
    )
    if (result?.job_id) {
      setJobId(result.job_id)
      showToast("Video job started", "info")
    }
  }

  return (
    <MediaPageLayout
      title="Video Processing"
      subtitle="H.264 MP4 compression and I-frame-based steganography"
      icon={<IconVideo />}
      accentColor="#a78bfa"
    >
      {/* Upload */}
      <Section title="1. Select MP4 File">
        <UploadDropzone
          onFileSelect={setSelectedFile}
          accept="video/*"
          selectedFileName={selectedFile?.name}
        />
      </Section>

      {/* Steganography */}
      <Section title="2. Steganography Settings">
        <MessageInput value={message} onChange={setMessage} />
        <EncryptionToggle
          isEnabled={encryptEnabled}
          onToggle={setEncryptEnabled}
          onPasswordChange={setPassword}
        />
      </Section>

      {/* CRF slider */}
      <Section title="3. Compression Quality (CRF)">
        <div style={{ display: "flex", flexDirection: "column", gap: "0.375rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: "0.875rem", color: "var(--color-muted)" }}>
              CRF <span style={{ color: "var(--color-muted-2)", fontSize: "0.8125rem" }}>(18 = highest quality, 51 = smallest file)</span>
            </span>
            <span style={{ fontWeight: 700, color: "var(--color-primary)", fontSize: "1.125rem" }}>{crf}</span>
          </div>
          <input
            type="range"
            min={18}
            max={51}
            value={crf}
            onChange={(e) => setCrf(Number(e.target.value))}
            style={{ width: "100%", accentColor: "var(--color-primary)" }}
            aria-label="CRF quality value"
          />
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "var(--color-muted-2)" }}>
            <span>Higher quality</span>
            <span>Smaller file</span>
          </div>
        </div>
      </Section>

      {/* Submit */}
      <Button onClick={handleUpload} disabled={!selectedFile || isUploading} isLoading={isUploading}>
        Embed Message in Video
      </Button>

      {/* Errors */}
      {(uploadError || pollingError) && (
        <ErrorBanner message={uploadError || pollingError || "Unknown error"} />
      )}

      {/* Upload progress */}
      {(isUploading || progress > 0) && <UploadProgress percent={progress} />}

      {/* Job result */}
      {status && status !== "done" && (
        <JobStatusPanel status={status} jobId={job?.job_id} />
      )}
      {status === "done" && job?.job_id && (
        <ResultPanel
          jobId={job.job_id}
          accentColor="#a78bfa"
        />
      )}
    </MediaPageLayout>
  )
}