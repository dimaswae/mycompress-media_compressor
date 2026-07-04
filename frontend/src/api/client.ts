
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
      const errorData: any = await response.json()
      error.code = errorData.error.code
    } catch {
      error.code = "UNKNOWN_ERROR"
    }
    throw error
  }

  return response.json() as Promise<T>
}

export async function uploadApi<T>(
  endpoint: string,
  formData: FormData,
  onProgress?: (progress: number) => void
): Promise<T> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open("POST", `${API_BASE}${endpoint}`)

    if (onProgress) {
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const percentComplete = Math.round((event.loaded / event.total) * 100)
          onProgress(percentComplete)
        }
      }
    }

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText) as T)
        } catch {
          reject(new Error("Failed to parse response JSON"))
        }
      } else {
        const error: ApiError = new Error("API request failed")
        try {
          const errorData = JSON.parse(xhr.responseText)
          error.code = errorData.error.code
        } catch {
          error.code = "UNKNOWN_ERROR"
        }
        reject(error)
      }
    }

    xhr.onerror = () => {
      reject(new Error("Network error during upload"))
    }

    xhr.send(formData)
  })
}