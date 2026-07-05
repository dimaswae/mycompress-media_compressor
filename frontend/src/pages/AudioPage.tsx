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
import * as audioApi from "../api/audioApi"
import { ErrorBanner } from "../components/common/ErrorBanner"
import { UploadProgress } from "../components/upload/UploadProgressNew"
import { useToast } from "../components/common/ToastContext"

const ACCENT = "#38bdf8"
const BITRATES = ["64k", "128k", "192k", "320k"]

function IconAudio() {
  return (
    <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 18V5l12-2v13" />
      <circle cx="6" cy="18" r="3" />
      <circle cx="18" cy="16" r="3" />
    </svg>
  )
}

export function AudioPage() {
  const [mode, setMode] = useState<PageMode>("compress")
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  // Compress-mode state
  const [bitrate, setBitrate] = useState("128k")
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

  const uploadError = rawUploadError ? friendlyError(rawUploadError, "audio") : null
  const pollingError = rawPollingError ? friendlyError(rawPollingError, "audio") : null

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
      audioApi.compressAudio(selectedFile, bitrate, onProgress)
    )
    if (result?.job_id) { setJobId(result.job_id); showToast("Compression started", "info") }
  }

  const handleDecompress = async () => {
    if (!selectedFile) return
    const result = await upload((onProgress) =>
      audioApi.decompressAudio(selectedFile, bitrate, onProgress)
    )
    if (result?.job_id) { setJobId(result.job_id); showToast("Decompression started", "info") }
  }

  /* ── Stego handlers ── */
  const handleEmbed = async () => {
    if (!selectedFile) return
    const result = await upload((onProgress) =>
      audioApi.embedMessage(selectedFile, message, encryptEnabled ? password : undefined, onProgress)
    )
    if (result?.job_id) { setJobId(result.job_id); showToast("Embedding started", "info") }
  }

  const handleExtract = async () => {
    if (!selectedFile) return
    const result = await upload((onProgress) =>
      audioApi.extractMessage(selectedFile, encryptEnabled ? password : undefined, onProgress)
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
          { id: false, label: "Compress (WAV → MP3)" },
          { id: true, label: "Decompress (MP3 → WAV)" },
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

      <Section title={isDecompress ? "1. Select MP3 File" : "1. Select WAV File"}>
        <p style={{ margin: 0, fontSize: "0.8125rem", color: "var(--color-muted)" }}>
          {isDecompress
            ? "Upload an MP3 file to decompress back to WAV."
            : "Upload a WAV audio file to compress to MP3. File must be in WAV format."}
        </p>
        <UploadDropzone
          onFileSelect={(f) => { setSelectedFile(f); resetJob() }}
          accept={isDecompress ? "audio/mpeg,.mp3" : "audio/wav,.wav"}
          selectedFileName={selectedFile?.name}
        />
      </Section>

      <Section title="2. Bitrate">
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          {BITRATES.map((br) => (
            <label
              key={br}
              style={{
                display: "flex", alignItems: "center", gap: "0.375rem",
                cursor: "pointer", padding: "0.5rem 1rem",
                background: bitrate === br ? `${ACCENT}1a` : "var(--color-surface-2)",
                border: `1px solid ${bitrate === br ? `${ACCENT}66` : "var(--color-border)"}`,
                borderRadius: "var(--radius-sm)", transition: "all 200ms",
                color: bitrate === br ? ACCENT : "var(--color-muted)",
                fontWeight: bitrate === br ? 600 : 500, fontSize: "0.9375rem",
              }}
            >
              <input
                type="radio" name="bitrate" value={br}
                checked={bitrate === br} onChange={() => setBitrate(br)}
                style={{ display: "none" }}
              />
              {br}
            </label>
          ))}
        </div>
        <p style={{ margin: 0, fontSize: "0.8125rem", color: "var(--color-muted)" }}>
          Lower bitrate = smaller file size but lower quality. 128k is a good balance for most use cases.
        </p>
      </Section>

      <Button
        onClick={isDecompress ? handleDecompress : handleCompress}
        disabled={!selectedFile || isUploading}
        isLoading={isUploading}
      >
        {isDecompress ? "Decompress to WAV" : "Compress to MP3"}
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

      <Section title="1. Select WAV File">
        <p style={{ margin: 0, fontSize: "0.8125rem", color: "var(--color-muted)" }}>
          Audio steganography requires an original <strong>WAV</strong> file — not MP3.
          LSB embedding works directly on PCM sample data.
        </p>
        <UploadDropzone
          onFileSelect={(f) => { setSelectedFile(f); resetJob() }}
          accept="audio/wav,.wav"
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
        {isExtract ? "Extract Hidden Message" : "Hide Message in Audio"}
      </Button>
    </>
  )

  return (
    <MediaPageLayout
      title="Audio Processing"
      subtitle="Compress WAV to MP3 or hide secret messages with LSB steganography"
      icon={<IconAudio />}
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