export interface ErrorResponse {
  code: string
  message: string
}

export interface JobStatusResponse {
  job_id: string
  status: string
  result_path?: string
  original_path?: string
  created_at: string
  updated_at: string
}