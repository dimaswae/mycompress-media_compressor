import { fetchApi, uploadApi } from "./client"
import type { ImageExtractResponse, ImageJobResponse, CompareResponse } from "../types/media"

export async function compressImage(
  file: File,
  algorithm: string,
  onProgress?: (progress: number) => void
): Promise<ImageJobResponse> {
  const form = new FormData()
  form.append("file", file)
  form.append("algorithm", algorithm)
  return uploadApi<ImageJobResponse>("/image/compress", form, onProgress)
}

export async function decompressImage(
  file: File,
  algorithm: string,
  onProgress?: (progress: number) => void
): Promise<ImageJobResponse> {
  const form = new FormData()
  form.append("file", file)
  form.append("algorithm", algorithm)
  return uploadApi<ImageJobResponse>("/image/decompress", form, onProgress)
}

export async function embedMessage(
  file: File,
  message: string,
  password?: string,
  algorithm?: string,
  onProgress?: (progress: number) => void
): Promise<ImageJobResponse> {
  const form = new FormData()
  form.append("file", file)
  form.append("message", message)
  if (password) form.append("password", password)
  if (algorithm) form.append("algorithm", algorithm)
  return uploadApi<ImageJobResponse>("/image/embed", form, onProgress)
}

export async function extractMessage(
  file: File,
  password?: string,
  algorithm?: string,
  onProgress?: (progress: number) => void
): Promise<ImageExtractResponse> {
  const form = new FormData()
  form.append("file", file)
  if (password) form.append("password", password)
  if (algorithm) form.append("algorithm", algorithm)
  return uploadApi<ImageExtractResponse>("/image/extract", form, onProgress)
}

export async function compareImage(jobId: string): Promise<CompareResponse> {
  return fetchApi<CompareResponse>(`/image/${jobId}/compare`)
}