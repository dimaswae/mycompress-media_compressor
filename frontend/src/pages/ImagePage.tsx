import { useEffect, useState } from "react"
import { UploadDropzone } from "../components/upload/UploadDropzoneNew"
import { Button } from "../components/common/Button"
import { MessageInput } from "../components/stego/MessageInput"
import { EncryptionToggle } from "../components/stego/EncryptionToggle"
import { CapacityIndicator } from "../components/stego/CapacityIndicator"
import { MediaPageLayout, Section, JobStatusPanel, ResultPanel } from "../components/common/MediaPageLayout"
import { ModeSelector, friendlyError } from "../components/common/ModeSelector"
import type { PageMode } from "../components/common/ModeSelector"
import { useFileUpload } from "../hooks/useFileUpload"
import { useJobPolling } from "../hooks/useJobPolling"
import * as imageApi from "../api/imageApi"
import { ErrorBanner } from "../components/common/ErrorBanner"
import { UploadProgress } from "../components/upload/UploadProgressNew"
import { useToast } from "../components/common/ToastContext"
import { ImageCompareView } from "../components/comparison/ImageCompareView"
import type { CompareResponse } from "../types/media"

const ACCENT = "#22c55e"

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

/* ─── Algorithm radio pills (shared by compress mode and stego mode) ─── */
function AlgoRadio({
  value,
  onChange,
  options,
}: {
  value: string
  onChange: (v: string) => void
  options: { id: string; label: string }[]
}) {
  return (
    <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
      {options.map(({ id, label }) => (
        <label
          key={id}
          style={{
            display: "flex", alignItems: "center", gap: "0.5rem",
            cursor: "pointer", padding: "0.5rem 1rem",
            background: value === id ? `${ACCENT}1a` : "var(--color-surface-2)",
            border: `1px solid ${value === id ? `${ACCENT}66` : "var(--color-border)"}`,
            borderRadius: "var(--radius-sm)",
            transition: "all 200ms",
            color: value === id ? ACCENT : "var(--color-muted)",
            fontWeight: value === id ? 600 : 500,
            fontSize: "0.9375rem",
          }}
        >
          <input
            type="radio"
            name="image-algo"
            value={id}
            checked={value === id}
            onChange={() => onChange(id)}
            style={{ display: "none" }}
          />
          {label}
        </label>
      ))}
    </div>
  )
}

export function ImagePage() {
  const [mode, setMode] = useState<PageMode>("compress")
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  // Compress-mode state
  const [compressAlgo, setCompressAlgo] = useState("rle")
  const [isDecompress, setIsDecompress] = useState(false)

  // Stego-mode state
  const [message, setMessage] = useState("")
  const [password, setPassword] = useState("")
  const [encryptEnabled, setEncryptEnabled] = useState(false)
  const [stegoAlgo, setStegoAlgo] = useState<string>("") // optional, compresses the message text
  const [isExtract, setIsExtract] = useState(false)
  const [capacity, setCapacity] = useState(0)
  const [extractedMessage, setExtractedMessage] = useState<string | null>(null)

  // Job state
  const [jobId, setJobId] = useState<string | null>(null)
  const [compareData, setCompareData] = useState<CompareResponse | null>(null)

  const { upload, progress, isUploading, error: rawUploadError } = useFileUpload()
  const { status, job, error: rawPollingError } = useJobPolling(jobId || "")
  const { showToast } = useToast()

  // Map raw errors to friendly messages
  const uploadError = rawUploadError ? friendlyError(rawUploadError, "image") : null
  const pollingError = rawPollingError ? friendlyError(rawPollingError, "image") : null

  // Reset job/result when mode or sub-mode changes
  const resetJob = () => {
    setJobId(null)
    setCompareData(null)
    setExtractedMessage(null)
  }

  const handleModeChange = (m: PageMode) => {
    setMode(m)
    setSelectedFile(null)
    resetJob()
  }

  // Fetch compare data after embed/compress finishes
  useEffect(() => {
    if (status === "done" && jobId && !isExtract) {
      imageApi.compareImage(jobId)
        .then(setCompareData)
        .catch((e) => showToast(`Failed to fetch comparison: ${e.message}`, "error"))
    } else {
      setCompareData(null)
    }
  }, [status, jobId, isExtract, showToast])

  const handleFileSelect = (file: File) => {
    setSelectedFile(file)
    resetJob()
    // Compute pixel capacity for stego mode
    const img = new globalThis.Image()
    img.src = URL.createObjectURL(file)
    img.onload = () => { setCapacity(img.width * img.height * 3); URL.revokeObjectURL(img.src) }
    img.onerror = () => { setCapacity(0); URL.revokeObjectURL(img.src) }
  }

  /* ── Compress mode handlers ── */
  const handleCompress = async () => {
    if (!selectedFile) return
    const result = await upload((onProgress) =>
      imageApi.compressImage(selectedFile, compressAlgo, onProgress)
    )
    if (result?.job_id) { setJobId(result.job_id); showToast("Compression started", "info") }
  }

  const handleDecompress = async () => {
    if (!selectedFile) return
    const result = await upload((onProgress) =>
      imageApi.decompressImage(selectedFile, compressAlgo, onProgress)
    )
    if (result?.job_id) { setJobId(result.job_id); showToast("Decompression started", "info") }
  }

  /* ── Stego mode handlers ── */
  const handleEmbed = async () => {
    if (!selectedFile) return
    const result = await upload((onProgress) =>
      imageApi.embedMessage(
        selectedFile, message,
        encryptEnabled ? password : undefined,
        stegoAlgo || undefined,
        onProgress,
      )
    )
    if (result?.job_id) { setJobId(result.job_id); showToast("Embedding started", "info") }
  }

  const handleExtract = async () => {
    if (!selectedFile) return
    const result = await upload((onProgress) =>
      imageApi.extractMessage(
        selectedFile,
        encryptEnabled ? password : undefined,
        stegoAlgo || undefined,
        onProgress,
      )
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
      {/* Sub-mode toggle: Compress vs Decompress */}
      <div style={{ display: "flex", gap: "0.5rem" }}>
        {[
          { id: false, label: "Compress" },
          { id: true, label: "Decompress" },
        ].map(({ id, label }) => (
          <button
            key={String(id)}
            onClick={() => { setIsDecompress(id); resetJob() }}
            style={{
              padding: "0.375rem 1rem",
              borderRadius: "var(--radius-sm)",
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

      <Section title="1. Select Image File">
        <UploadDropzone
          onFileSelect={handleFileSelect}
          accept="image/*"
          selectedFileName={selectedFile?.name}
        />
      </Section>

      <Section title="2. Compression Algorithm">
        <AlgoRadio
          value={compressAlgo}
          onChange={setCompressAlgo}
          options={[
            { id: "rle", label: "RLE" },
            { id: "huffman", label: "Huffman" },
          ]}
        />
      </Section>

      <Button
        onClick={isDecompress ? handleDecompress : handleCompress}
        disabled={!selectedFile || isUploading}
        isLoading={isUploading}
      >
        {isDecompress ? "Decompress Image" : "Compress Image"}
      </Button>
    </>
  )

  const renderStegoMode = () => (
    <>
      {/* Sub-mode toggle: Embed vs Extract */}
      <div style={{ display: "flex", gap: "0.5rem" }}>
        {[
          { id: false, label: "Hide Message" },
          { id: true, label: "Extract Message" },
        ].map(({ id, label }) => (
          <button
            key={String(id)}
            onClick={() => { setIsExtract(id); resetJob(); setExtractedMessage(null) }}
            style={{
              padding: "0.375rem 1rem",
              borderRadius: "var(--radius-sm)",
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

      <Section title="1. Select Image File">
        <UploadDropzone
          onFileSelect={handleFileSelect}
          accept="image/*"
          selectedFileName={selectedFile?.name}
        />
      </Section>

      {!isExtract && (
        <Section title="2. Secret Message">
          <MessageInput value={message} onChange={setMessage} />
          {capacity > 0 && (
            <CapacityIndicator
              messageLength={message.length}
              capacityBits={capacity}
              isEncryptionEnabled={encryptEnabled}
            />
          )}
        </Section>
      )}

      <Section title={isExtract ? "2. Security" : "3. Security"}>
        <EncryptionToggle
          isEnabled={encryptEnabled}
          onToggle={(v) => { setEncryptEnabled(v); if (!v) setPassword("") }}
          onPasswordChange={setPassword}
        />
      </Section>

      {/* Optional: compress the hidden message text (NOT the image) */}
      {!isExtract && (
        <Section title={`${isExtract ? "3" : "4"}. Compress hidden message (optional)`}>
          <p style={{ margin: 0, fontSize: "0.8125rem", color: "var(--color-muted)", lineHeight: 1.5 }}>
            This compresses the <strong>secret text</strong> before hiding it — it does
            <strong> not</strong> compress the image itself. Leave blank to skip.
          </p>
          <AlgoRadio
            value={stegoAlgo}
            onChange={(v) => setStegoAlgo(stegoAlgo === v ? "" : v)}
            options={[
              { id: "rle", label: "RLE (text)" },
              { id: "huffman", label: "Huffman (text)" },
            ]}
          />
          {stegoAlgo && (
            <button
              onClick={() => setStegoAlgo("")}
              style={{
                alignSelf: "flex-start", padding: "0.25rem 0.75rem",
                border: "1px solid var(--color-border)", borderRadius: "var(--radius-sm)",
                background: "transparent", color: "var(--color-muted)",
                fontSize: "0.8125rem", cursor: "pointer",
              }}
            >
              ✕ Clear (no compression)
            </button>
          )}
        </Section>
      )}

      <Button
        onClick={isExtract ? handleExtract : handleEmbed}
        disabled={!selectedFile || isUploading || (!isExtract && !message.trim())}
        isLoading={isUploading}
      >
        {isExtract ? "Extract Hidden Message" : "Hide Message in Image"}
      </Button>
    </>
  )

  return (
    <MediaPageLayout
      title="Image Processing"
      subtitle="Compress PNG/JPEG files or hide secret messages with LSB steganography"
      icon={<IconImage />}
      accentColor={ACCENT}
    >
      {/* ── Mode selector ── */}
      <ModeSelector mode={mode} onChange={handleModeChange} accentColor={ACCENT} />

      {/* ── Mode-specific form ── */}
      {mode === "compress" ? renderCompressMode() : renderStegoMode()}

      {/* ── Shared: errors ── */}
      {(uploadError || pollingError) && (
        <ErrorBanner message={uploadError || pollingError || "Unknown error"} />
      )}

      {/* ── Shared: progress ── */}
      {(isUploading || progress > 0) && <UploadProgress percent={progress} />}

      {/* ── Shared: in-progress banner ── */}
      {status && status !== "done" && (
        <JobStatusPanel status={status} jobId={job?.job_id} />
      )}

      {/* ── Shared: result panel ── */}
      {status === "done" && job?.job_id && (
        <>
          {/* Extract result: show the extracted text prominently */}
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

          {/* Download + compare + metrics for non-extract operations */}
          {!isExtract && (
            <ResultPanel
              jobId={job.job_id}
              originalSize={compareData?.original_size}
              resultSize={compareData?.result_size}
              metrics={compareData?.metrics}
              accentColor={ACCENT}
            >
              {compareData && (
                <ImageCompareView
                  originalUrl={getAbsoluteUrl(compareData.original_url)}
                  resultUrl={getAbsoluteUrl(compareData.result_url)}
                />
              )}
            </ResultPanel>
          )}
        </>
      )}
    </MediaPageLayout>
  )
}