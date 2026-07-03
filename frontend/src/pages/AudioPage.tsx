import React, { useState } from "react"
import { UploadDropzone } from "../components/upload/UploadDropzone"
import { Button } from "../components/common/Button"
import { MessageInput } from "../components/stego/MessageInput"
import { EncryptionToggle } from "../components/stego/EncryptionToggle"
import { useFileUpload } from "../hooks/useFileUpload"
import { useJobPolling } from "../hooks/useJobPolling"
import * as audioApi from "../api/audioApi"
import { ErrorBanner } from "../components/common/ErrorBanner"

export function AudioPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [message, setMessage] = useState("")
  const [password, setPassword] = useState("")
  const [encryptEnabled, setEncryptEnabled] = useState(false)
  const [jobId, setJobId] = useState<string | null>(null)

  const { upload } = useFileUpload()
  const { status, job, error } = useJobPolling(jobId || "")

  const handleUpload = async () => {
    if (!selectedFile) return
    const result = await upload(() =>
      audioApi.embedMessage(selectedFile, message, encryptEnabled ? password : undefined)
    )
    if (result?.job_id) setJobId(result.job_id)
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-4">Audio Processing</h1>

      <div className="space-y-4">
        <UploadDropzone onFileSelect={setSelectedFile} accept="audio/*" />

        <MessageInput value={message} onChange={setMessage} />

        <EncryptionToggle
          isEnabled={encryptEnabled}
          onToggle={setEncryptEnabled}
          onPasswordChange={setPassword}
        />

        <Button onClick={handleUpload} disabled={!selectedFile}>
          Embed Message
        </Button>

        {error && <ErrorBanner message={error} />}

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