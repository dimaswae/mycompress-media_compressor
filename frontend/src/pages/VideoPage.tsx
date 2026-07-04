import { useState } from "react"
import { UploadDropzone } from "../components/upload/UploadDropzoneNew"
import { Button } from "../components/common/Button"
import { MessageInput } from "../components/stego/MessageInput"
import { EncryptionToggle } from "../components/stego/EncryptionToggle"
import { useFileUpload } from "../hooks/useFileUpload"
import { useJobPolling } from "../hooks/useJobPolling"
import * as videoApi from "../api/videoApi"
import { ErrorBanner } from "../components/common/ErrorBanner"
import { UploadProgress } from "../components/upload/UploadProgressNew"

export function VideoPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [message, setMessage] = useState("")
  const [password, setPassword] = useState("")
  const [encryptEnabled, setEncryptEnabled] = useState(false)
  const [crf, setCrf] = useState(28)
  const [jobId, setJobId] = useState<string | null>(null)

  const { upload, progress, isUploading, error: uploadError } = useFileUpload()
  const { status, job, error: pollingError } = useJobPolling(jobId || "")

  const handleUpload = async () => {
    if (!selectedFile) return
    const result = await upload((onProgress) =>
      videoApi.embedMessage(selectedFile, message, encryptEnabled ? password : undefined, onProgress)
    )
    if (result?.job_id) setJobId(result.job_id)
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-4">Video Processing</h1>

      <div className="space-y-4">
        <UploadDropzone onFileSelect={setSelectedFile} accept="video/*" />

        <MessageInput value={message} onChange={setMessage} />

        <EncryptionToggle
          isEnabled={encryptEnabled}
          onToggle={setEncryptEnabled}
          onPasswordChange={setPassword}
        />

        <label className="flex items-center gap-2 text-white">
          <span>CRF:</span>
          <input
            type="number"
            min={18}
            max={51}
            value={crf}
            onChange={(e) => setCrf(Number(e.target.value))}
            className="w-20 bg-gray-800 border border-gray-600 rounded p-1"
          />
        </label>

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
          <div className="mt-4 p-4 bg-gray-800 rounded">
            <p className="text-white">Job Status: {status}</p>
            {job && <p className="text-gray-400">Job ID: {job.job_id}</p>}
          </div>
        )}
      </div>
    </div>
  )
}