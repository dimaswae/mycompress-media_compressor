import React, { useState } from "react"
import { UploadDropzone } from "../components/upload/UploadDropzone"
import { Button } from "../components/common/Button"
import { MessageInput } from "../components/stego/MessageInput"
import { EncryptionToggle } from "../components/stego/EncryptionToggle"
import { CapacityIndicator } from "../components/stego/CapacityIndicator"
import { useFileUpload } from "../hooks/useFileUpload"
import { useJobPolling } from "../hooks/useJobPolling"
import * as imageApi from "../api/imageApi"
import { ErrorBanner } from "../components/common/ErrorBanner"

export function ImagePage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [message, setMessage] = useState("")
  const [password, setPassword] = useState("")
  const [encryptEnabled, setEncryptEnabled] = useState(false)
  const [algo, setAlgo] = useState("rle")
  const [jobId, setJobId] = useState<string | null>(null)
  const [capacity, setCapacity] = useState(0)

  const { upload } = useFileUpload()
  const { status, job, error } = useJobPolling(jobId || "")

  const handleUpload = async () => {
    if (!selectedFile) return
    const result = await upload(() =>
      imageApi.embedMessage(selectedFile, message, encryptEnabled ? password : undefined, algo || undefined)
    )
    if (result?.job_id) setJobId(result.job_id)
  }

  const handleFileSelect = (file: File) => {
    setSelectedFile(file)
    // Estimate capacity: assume 100x100 image
    setCapacity(100 * 100 * 3)
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

        <CapacityIndicator messageLength={message.length} capacityBits={capacity} />

        <select
          className="bg-gray-800 border border-gray-600 rounded p-2 text-white"
          value={algo}
          onChange={(e) => setAlgo(e.target.value)}
        >
          <option value="rle">RLE</option>
          <option value="huffman">Huffman</option>
        </select>

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