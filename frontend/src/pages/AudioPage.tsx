import { useState } from "react"
import { UploadDropzone } from "../components/upload/UploadDropzoneNew"
import { Button } from "../components/common/Button"
import { MessageInput } from "../components/stego/MessageInput"
import { EncryptionToggle } from "../components/stego/EncryptionToggle"
import { MediaPageLayout, Section, JobStatusPanel } from "../components/common/MediaPageLayout"
import { useFileUpload } from "../hooks/useFileUpload"
import { useJobPolling } from "../hooks/useJobPolling"
import * as audioApi from "../api/audioApi"
import { ErrorBanner } from "../components/common/ErrorBanner"
import { UploadProgress } from "../components/upload/UploadProgressNew"
import { useToast } from "../components/common/ToastContext"

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
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [message, setMessage] = useState("")
  const [password, setPassword] = useState("")
  const [encryptEnabled, setEncryptEnabled] = useState(false)
  const [jobId, setJobId] = useState<string | null>(null)

  const { upload, progress, isUploading, error: uploadError } = useFileUpload()
  const { status, job, error: pollingError } = useJobPolling(jobId || "")
  const { showToast } = useToast()

  const handleUpload = async () => {
    if (!selectedFile) return
    const result = await upload((onProgress) =>
      audioApi.embedMessage(selectedFile, message, encryptEnabled ? password : undefined, onProgress)
    )
    if (result?.job_id) {
      setJobId(result.job_id)
      showToast("Audio job started", "info")
    }
  }

  return (
    <MediaPageLayout
      title="Audio Processing"
      subtitle="Compress WAV to MP3 and embed hidden messages with LSB steganography"
      icon={<IconAudio />}
      accentColor="#38bdf8"
    >
      {/* Upload */}
      <Section title="1. Select WAV File">
        <UploadDropzone
          onFileSelect={setSelectedFile}
          accept="audio/*"
          selectedFileName={selectedFile?.name}
        />
      </Section>

      {/* Stego settings */}
      <Section title="2. Steganography Settings">
        <MessageInput value={message} onChange={setMessage} />
        <EncryptionToggle
          isEnabled={encryptEnabled}
          onToggle={setEncryptEnabled}
          onPasswordChange={setPassword}
        />
      </Section>

      {/* Submit */}
      <Button onClick={handleUpload} disabled={!selectedFile || isUploading} isLoading={isUploading}>
        Embed Message in Audio
      </Button>

      {/* Errors */}
      {(uploadError || pollingError) && (
        <ErrorBanner message={uploadError || pollingError || "Unknown error"} />
      )}

      {/* Upload progress */}
      {(isUploading || progress > 0) && <UploadProgress percent={progress} />}

      {/* Job result */}
      {status && (
        <Section title="Result">
          <JobStatusPanel status={status} jobId={job?.job_id} />
        </Section>
      )}
    </MediaPageLayout>
  )
}