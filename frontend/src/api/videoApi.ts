import { fetchApi, uploadApi } from "./client"
import type { VideoExtractResponse, VideoJobResponse } from "../types/media"

export async function compressVideo(
  file: File,
  crf: number = 28,
  onProgress?: (progress: number) => void
): Promise<VideoJobResponse> {
  const form = new FormData()
  form.append("file", file)
  form.append("crf", String(crf))
  return uploadApi<VideoJobResponse>("/video/compress", form, onProgress)
}

export async function decompressVideo(
  file: File,
  onProgress?: (progress: number) => void
): Promise<VideoJobResponse> {
  const form = new FormData()
  form.append("file", file)
  return uploadApi<VideoJobResponse>("/video/decompress", form, onProgress)
}

export async function embedMessage(
  file: File,
  message: string,
  password?: string,
  onProgress?: (progress: number) => void
): Promise<VideoJobResponse> {
  const form = new FormData()
  form.append("file", file)
  form.append("message", message)
  if (password) form.append("password", password)
  return uploadApi<VideoJobResponse>("/video/embed", form, onProgress)
}

export async function extractMessage(
  file: File,
  password?: string,
  onProgress?: (progress: number) => void
): Promise<VideoExtractResponse> {
  const form = new FormData()
  form.append("file", file)
  if (password) form.append("password", password)
  return uploadApi<VideoExtractResponse>("/video/extract", form, onProgress)
}

export async function compareVideo(jobId: string): Promise<VideoExtractResponse> {
  return fetchApi<VideoExtractResponse>(`/video/${jobId}/compare`)
}