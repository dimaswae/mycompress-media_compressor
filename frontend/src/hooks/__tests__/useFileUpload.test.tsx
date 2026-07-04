import { describe, it, expect, vi } from "vitest"
import { renderHook, act } from "@testing-library/react"
import { useFileUpload } from "../useFileUpload"

describe("useFileUpload", () => {
  it("tracks upload progress incrementally using the callback", async () => {
    const mockUploadResponse = { job_id: "test-job-id" }

    // Simulate an upload task that calls onProgress multiple times
    const mockUploadFn = vi.fn().mockImplementation(async (onProgress) => {
      onProgress(10)
      onProgress(50)
      onProgress(90)
      return mockUploadResponse
    })

    const { result } = renderHook(() => useFileUpload())

    expect(result.current.progress).toBe(0)
    expect(result.current.isUploading).toBe(false)

    let uploadPromise: any
    act(() => {
      uploadPromise = result.current.upload(mockUploadFn)
    })

    // Progress updates should be captured
    expect(result.current.progress).toBe(90)
    expect(result.current.isUploading).toBe(true)

    await act(async () => {
      const res = await uploadPromise
      expect(res).toEqual(mockUploadResponse)
    })

    // Final state
    expect(result.current.progress).toBe(100)
    expect(result.current.isUploading).toBe(false)
    expect(result.current.result).toEqual(mockUploadResponse)
  })

  it("handles upload errors correctly", async () => {
    const mockUploadFn = vi.fn().mockImplementation(async () => {
      throw new Error("Upload failed")
    })

    const { result } = renderHook(() => useFileUpload())

    let uploadPromise: any
    act(() => {
      uploadPromise = result.current.upload(mockUploadFn)
    })

    await act(async () => {
      await uploadPromise
    })

    expect(result.current.error).toBe("Upload failed")
    expect(result.current.isUploading).toBe(false)
  })
})
