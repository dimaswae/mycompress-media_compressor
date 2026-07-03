import { fetchApi } from "./client"
import type { JobStatusResponse } from "../types/job"

export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  return fetchApi<JobStatusResponse>(`/jobs/${jobId}`)
}

export async function downloadResult(jobId: string): Promise<Blob> {
  const response = await fetch(`${import.meta.env.VITE_API_BASE || "/api/v1"}/jobs/${jobId}/download`)
  if (!response.ok) {
    throw new Error("Failed to download result")
  }
  return response.blob()
}

export async function listJobs(
  limit = 20,
  offset = 0
): Promise<JobStatusResponse[]> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  })
  const data = await fetchApi<{ jobs: JobStatusResponse[] }>(`/jobs?${params}`)
  return data.jobs
}