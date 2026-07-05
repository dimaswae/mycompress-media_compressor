import { useState } from "react"
import { UploadDropzone } from "../components/upload/UploadDropzoneNew"
import { Button } from "../components/common/Button"
import { MessageInput } from "../components/stego/MessageInput"
import { EncryptionToggle } from "../components/stego/EncryptionToggle"
import { MediaPageLayout, Section, JobStatusPanel, ResultPanel } from "../components/common/MediaPageLayout"
import { ModeSelector, friendlyError } from "../components/common/ModeSelector"
import type { PageMode } from "../components/common/ModeSelector"
import { useFileUpload } from "../hooks/useFileUpload"
import { useJobPolling } from "../hooks/useJobPolling"
import * as videoApi from "../api/videoApi"
import { ErrorBanner } from "../components/common/ErrorBanner"
import { UploadProgress } from "../components/upload/UploadProgressNew"
import { useToast } from "../components/common/ToastContext"

const ACCENT = "#a78bfa"

function IconVideo() {
  return (
    <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="23 7 16 12 23 17 23 7" />
      <rect x="1" y="5" width="15" height="14" rx="2" />
    </svg>
  )
}

export function VideoPage() {
  const [mode, setMode] = useState<PageMode>("compress")
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  // Compress-mode state
  const [crf, setCrf] = useState(28)
  const [isDecompress, setIsDecompress] = useState(false)

  // Stego-mode state
  const [message, setMessage] = useState("")
  const [password, setPassword] = useState("")
  const [encryptEnabled, setEncryptEnabled] = useState(false)
  const [isExtract, setIsExtract] = useState(false)
  const [extractedMessage, setExtractedMessage] = useState<string | null>(null)

  // Job state
  const [jobId, setJobId] = useState<string | null>(null)

  const { upload, progress, isUploading, error: rawUploadError } = useFileUpload()
  const { status, job, error: rawPollingError } = useJobPolling(jobId || "")
  const { showToast } = useToast()

  const uploadError = rawUploadError ? friendlyError(rawUploadError, "video") : null
  const pollingError = rawPollingError ? friendlyError(rawPollingError, "video") : null

  const resetJob = () => { setJobId(null); setExtractedMessage(null) }

  const handleModeChange = (m: PageMode) => {
    setMode(m)
    setSelectedFile(null)
    resetJob()
  }

  /* ── Compress handlers ── */
  const handleCompress = async () => {
    if (!selectedFile) return
    const result = await upload((onProgress) =>
      videoApi.compressVideo(selectedFile, crf, onProgress)
    )
    if (result?.job_id) { setJobId(result.job_id); showToast("Compression started", "info") }
  }

  const handleDecompress = async () => {
    if (!selectedFile) return
    const result = await upload((onProgress) =>
      videoApi.decompressVideo(selectedFile, onProgress)
    )
    if (result?.job_id) { setJobId(result.job_id); showToast("Decompression started", "info") }
  }

  /* ── Stego handlers ── */
  const handleEmbed = async () => {
    if (!selectedFile) return
    const result = await upload((onProgress) =>
      videoApi.embedMessage(selectedFile, message, encryptEnabled ? password : undefined, onProgress)
    )
    if (result?.job_id) { setJobId(result.job_id); showToast("Embedding started", "info") }
  }

  const handleExtract = async () => {
    if (!selectedFile) return
    const result = await upload((onProgress) =>
      videoApi.extractMessage(selectedFile, encryptEnabled ? password : undefined, onProgress)
    )
    if (result?.job_id) {
      setJobId(result.job_id)
      setExtractedMessage((result as any).message ?? null)
      showToast("Extraction complete", "success")
    }
  }

  /* ── Render helpers ── */
  const renderCompressMode = () => (
    <>
      <div style={{ display: "flex", gap: "0.5rem" }}>
        {[
          { id: false, label: "Compress" },
          { id: true, label: "Decompress" },
        ].map(({ id, label }) => (
          <button
            key={String(id)}
            onClick={() => { setIsDecompress(id); resetJob() }}
            style={{
              padding: "0.375rem 1rem", borderRadius: "var(--radius-sm)",
              border: `1px solid ${isDecompress === id ? `${ACCENT}66` : "var(--color-border)"}`,
              background: isDecompress === id ? `${ACCENT}1a` : "transparent",
              color: isDecompress === id ? ACCENT : "var(--color-muted)",
              fontWeight: isDecompress === id ? 700 : 500,
              cursor: "pointer", fontSize: "0.875rem", transition: "all 180ms",
            }}
          >
            {label}
          </button>
        ))}
      </div>

      <Section title="1. Select MP4 File">
        <UploadDropzone
          onFileSelect={(f) => { setSelectedFile(f); resetJob() }}
          accept="video/mp4,.mp4"
          selectedFileName={selectedFile?.name}
        />
      </Section>

      {!isDecompress && (
        <Section title="2. Compression Quality (CRF)">
          <div style={{ display: "flex", flexDirection: "column", gap: "0.375rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "0.875rem", color: "var(--color-muted)" }}>
                CRF <span style={{ color: "var(--color-muted-2)", fontSize: "0.8125rem" }}>(18 = highest quality, 51 = smallest file)</span>
              </span>
              <span style={{ fontWeight: 700, color: ACCENT, fontSize: "1.125rem" }}>{crf}</span>
            </div>
            <input
              type="range" min={18} max={51} value={crf}
              onChange={(e) => setCrf(Number(e.target.value))}
              style={{ width: "100%", accentColor: ACCENT }}
              aria-label="CRF quality value"
            />
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "var(--color-muted-2)" }}>
              <span>Higher quality</span>
              <span>Smaller file</span>
            </div>
          </div>
        </Section>
      )}

      <Button
        onClick={isDecompress ? handleDecompress : handleCompress}
        disabled={!selectedFile || isUploading}
        isLoading={isUploading}
      >
        {isDecompress ? "Decompress Video" : "Compress Video"}
      </Button>
    </>
  )

  const renderStegoMode = () => (
    <>
      <div style={{ display: "flex", gap: "0.5rem" }}>
        {[
          { id: false, label: "Hide Message" },
          { id: true, label: "Extract Message" },
        ].map(({ id, label }) => (
          <button
            key={String(id)}
            onClick={() => { setIsExtract(id); resetJob(); setExtractedMessage(null) }}
            style={{
              padding: "0.375rem 1rem", borderRadius: "var(--radius-sm)",
              border: `1px solid ${isExtract === id ? `${ACCENT}66` : "var(--color-border)"}`,
              background: isExtract === id ? `${ACCENT}1a` : "transparent",
              color: isExtract === id ? ACCENT : "var(--color-muted)",
              fontWeight: isExtract === id ? 700 : 500,
              cursor: "pointer", fontSize: "0.875rem", transition: "all 180ms",
            }}
          >
            {label}
          </button>
        ))}
      </div>

      <Section title="1. Select MP4 File">
        <p style={{ margin: 0, fontSize: "0.8125rem", color: "var(--color-muted)" }}>
          Upload an MP4 video file. The message will be hidden in the video's I-frames using LSB steganography.
        </p>
        <UploadDropzone
          onFileSelect={(f) => { setSelectedFile(f); resetJob() }}
          accept="video/mp4,.mp4"
          selectedFileName={selectedFile?.name}
        />
      </Section>

      {!isExtract && (
        <Section title="2. Secret Message">
          <MessageInput value={message} onChange={setMessage} />
        </Section>
      )}

      <Section title={isExtract ? "2. Security" : "3. Security"}>
        <EncryptionToggle
          isEnabled={encryptEnabled}
          onToggle={(v) => { setEncryptEnabled(v); if (!v) setPassword("") }}
          onPasswordChange={setPassword}
        />
      </Section>

      <Button
        onClick={isExtract ? handleExtract : handleEmbed}
        disabled={!selectedFile || isUploading || (!isExtract && !message.trim())}
        isLoading={isUploading}
      >
        {isExtract ? "Extract Hidden Message" : "Hide Message in Video"}
      </Button>
    </>
  )

  return (
    <MediaPageLayout
      title="Video Processing"
      subtitle="H.264 MP4 compression or I-frame-based LSB steganography"
      icon={<IconVideo />}
      accentColor={ACCENT}
    >
      <ModeSelector mode={mode} onChange={handleModeChange} accentColor={ACCENT} />

      {mode === "compress" ? renderCompressMode() : renderStegoMode()}

      {(uploadError || pollingError) && (
        <ErrorBanner message={uploadError || pollingError || "Unknown error"} />
      )}

      {(isUploading || progress > 0) && <UploadProgress percent={progress} />}

      {status && status !== "done" && (
        <JobStatusPanel status={status} jobId={job?.job_id} />
      )}

      {status === "done" && job?.job_id && (
        <>
          {isExtract && extractedMessage !== null && (
            <div className="card" style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              <h2 style={{ margin: 0, fontSize: "0.9375rem", fontWeight: 700, color: "var(--color-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
                Extracted Message
              </h2>
              <div style={{
                padding: "0.875rem", background: "var(--color-surface-2)",
                borderRadius: "var(--radius-sm)", fontFamily: "ui-monospace, monospace",
                fontSize: "0.9rem", lineHeight: 1.6, color: "var(--color-text)",
                wordBreak: "break-word", whiteSpace: "pre-wrap",
                border: "1px solid var(--color-border)",
              }}>
                {extractedMessage || <em style={{ color: "var(--color-muted)" }}>(empty message)</em>}
              </div>
            </div>
          )}

          {!isExtract && (
            <ResultPanel jobId={job.job_id} accentColor={ACCENT} />
          )}
        </>
      )}
    </MediaPageLayout>
  )
}