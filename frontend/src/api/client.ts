import { ErrorResponse } from "../types/job"

const API_BASE = import.meta.env.VITE_API_BASE || "/api/v1"

export interface ApiError extends Error {
  code?: string
}

export async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, options)

  if (!response.ok) {
    const error: ApiError = new Error("API request failed")
    try {
      const errorData: ErrorResponse = await response.json()
      error.code = errorData.code
    } catch {
      error.code = "UNKNOWN_ERROR"
    }
    throw error
  }

  return response.json() as Promise<T>
}