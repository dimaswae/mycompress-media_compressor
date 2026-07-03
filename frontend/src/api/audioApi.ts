import { fetchApi } from "./client"
import type { AudioExtractResponse, AudioJobResponse } from "../types/media"

export async function compressAudio(
  file: File,
  bitrate: string = "128k"
): Promise<AudioJobResponse> {
  const form = new FormData()
  form.append("file", file)
  form.append("bitrate", bitrate)
  return fetchApi<AudioJobResponse>("/audio/compress", {
    method: "POST",
    body: form,
  })
}

export async function decompressAudio(
  file: File,
  bitrate: string = "128k"
): Promise<AudioJobResponse> {
  const form = new FormData()
  form.append("file", file)
  form.append("bitrate", bitrate)
  return fetchApi<AudioJobResponse>("/audio/decompress", {
    method: "POST",
    body: form,
  })
}

export async function embedMessage(
  file: File,
  message: string,
  password?: string
): Promise<AudioJobResponse> {
  const form = new FormData()
  form.append("file", file)
  form.append("message", message)
  if (password) form.append("password", password)
  return fetchApi<AudioJobResponse>("/audio/embed", {
    method: "POST",
    body: form,
  })
}

export async function extractMessage(
  file: File,
  password?: string
): Promise<AudioExtractResponse> {
  const form = new FormData()
  form.append("file", file)
  if (password) form.append("password", password)
  return fetchApi<AudioExtractResponse>("/audio/extract", {
    method: "POST",
    body: form,
  })
}

export async function compareAudio(jobId: string): Promise<AudioExtractResponse> {
  return fetchApi<AudioExtractResponse>(`/audio/${jobId}/compare`)
}