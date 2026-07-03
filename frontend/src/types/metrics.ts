export interface Metrics {
  [key: string]: number
}

export interface CompareResponse {
  job_id: string
  original_size: number
  result_size: number
  metrics: Metrics
}