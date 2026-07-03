import { fetchApi } from "./client"
import type { ImageExtractResponse, ImageJobResponse } from "../types/media"

export async function compressImage(
  file: File,
  algorithm: string
): Promise<ImageJobResponse> {
  const form = new FormData()
  form.append("file", file)
  form.append("algorithm", algorithm)
  return fetchApi<ImageJobResponse>("/image/compress", {
    method: "POST",
    body: form,
  })
}

export async function decompressImage(
  file: File,
  algorithm: string
): Promise<ImageJobResponse> {
  const form = new FormData()
  form.append("file", file)
  form.append("algorithm", algorithm)
  return fetchApi<ImageJobResponse>("/image/decompress", {
    method: "POST",
    body: form,
  })
}

export async function embedMessage(
  file: File,
  message: string,
  password?: string,
  algorithm?: string
): Promise<ImageJobResponse> {
  const form = new FormData()
  form.append("file", file)
  form.append("message", message)
  if (password) form.append("password", password)
  if (algorithm) form.append("algorithm", algorithm)
  return fetchApi<ImageJobResponse>("/image/embed", {
    method: "POST",
    body: form,
  })
}

export async function extractMessage(
  file: File,
  password?: string,
  algorithm?: string
): Promise<ImageExtractResponse> {
  const form = new FormData()
  form.append("file", file)
  if (password) form.append("password", password)
  if (algorithm) form.append("algorithm", algorithm)
  return fetchApi<ImageExtractResponse>("/image/extract", {
    method: "POST",
    body: form,
  })
}

export async function compareImage(jobId: string): Promise<ImageExtractResponse> {
  return fetchApi<ImageExtractResponse>(`/image/${jobId}/compare`)
}