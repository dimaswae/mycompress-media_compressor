import { fetchApi, uploadApi } from "./client"
import type { AudioExtractResponse, AudioJobResponse } from "../types/media"

export async function compressAudio(
  file: File,
  bitrate: string = "128k",
  onProgress?: (progress: number) => void
): Promise<AudioJobResponse> {
  const form = new FormData()
  form.append("file", file)
  form.append("bitrate", bitrate)
  return uploadApi<AudioJobResponse>("/audio/compress", form, onProgress)
}

export async function decompressAudio(
  file: File,
  bitrate: string = "128k",
  onProgress?: (progress: number) => void
): Promise<AudioJobResponse> {
  const form = new FormData()
  form.append("file", file)
  form.append("bitrate", bitrate)
  return uploadApi<AudioJobResponse>("/audio/decompress", form, onProgress)
}

export async function embedMessage(
  file: File,
  message: string,
  password?: string,
  onProgress?: (progress: number) => void
): Promise<AudioJobResponse> {
  const form = new FormData()
  form.append("file", file)
  form.append("message", message)
  if (password) form.append("password", password)
  return uploadApi<AudioJobResponse>("/audio/embed", form, onProgress)
}

export async function extractMessage(
  file: File,
  password?: string,
  onProgress?: (progress: number) => void
): Promise<AudioExtractResponse> {
  const form = new FormData()
  form.append("file", file)
  if (password) form.append("password", password)
  return uploadApi<AudioExtractResponse>("/audio/extract", form, onProgress)
}

export async function compareAudio(jobId: string): Promise<AudioExtractResponse> {
  return fetchApi<AudioExtractResponse>(`/audio/${jobId}/compare`)
}