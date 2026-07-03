export type MediaType = "image" | "audio" | "video"

export interface ImageJobResponse {
  job_id: string
  status: string
  metrics: Record<string, number>
}

export interface ImageExtractResponse {
  job_id: string
  message: string
  metrics: Record<string, number>
}

export interface AudioJobResponse {
  job_id: string
  status: string
  metrics: Record<string, number>
}

export interface AudioExtractResponse {
  job_id: string
  message: string
  metrics: Record<string, number>
}

export interface VideoJobResponse {
  job_id: string
  status: string
  metrics: Record<string, number>
}

export interface VideoExtractResponse {
  job_id: string
  message: string
  metrics: Record<string, number>
}