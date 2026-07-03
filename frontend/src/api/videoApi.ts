import { fetchApi } from "./client"
import type { VideoExtractResponse, VideoJobResponse } from "../types/media"

export async function compressVideo(
  file: File,
  crf: number = 28
): Promise<VideoJobResponse> {
  const form = new FormData()
  form.append("file", file)
  form.append("crf", String(crf))
  return fetchApi<VideoJobResponse>("/video/compress", {
    method: "POST",
    body: form,
  })
}

export async function decompressVideo(file: File): Promise<VideoJobResponse> {
  const form = new FormData()
  form.append("file", file)
  return fetchApi<VideoJobResponse>("/video/decompress", {
    method: "POST",
    body: form,
  })
}

export async function embedMessage(
  file: File,
  message: string,
  password?: string
): Promise<VideoJobResponse> {
  const form = new FormData()
  form.append("file", file)
  form.append("message", message)
  if (password) form.append("password", password)
  return fetchApi<VideoJobResponse>("/video/embed", {
    method: "POST",
    body: form,
  })
}

export async function extractMessage(
  file: File,
  password?: string
): Promise<VideoExtractResponse> {
  const form = new FormData()
  form.append("file", file)
  if (password) form.append("password", password)
  return fetchApi<VideoExtractResponse>("/video/extract", {
    method: "POST",
    body: form,
  })
}

export async function compareVideo(jobId: string): Promise<VideoExtractResponse> {
  return fetchApi<VideoExtractResponse>(`/video/${jobId}/compare`)
}