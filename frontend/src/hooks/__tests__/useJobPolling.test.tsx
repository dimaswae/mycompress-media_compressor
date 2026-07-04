import { describe, it, expect, vi, beforeEach } from "vitest"
import { renderHook, waitFor } from "@testing-library/react"
import { useJobPolling } from "../useJobPolling"
import { getJobStatus } from "../../api/jobsApi"

// Mock the API module
vi.mock("../../api/jobsApi", () => ({
  getJobStatus: vi.fn(),
}))

describe("useJobPolling", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("should stop polling when job status is done", async () => {
    const mockGetJobStatus = vi.mocked(getJobStatus)
    
    // First call returns "processing", second returns "done"
    mockGetJobStatus
      .mockResolvedValueOnce({
        id: "job-A",
        status: "processing",
        media_type: "image",
        operation: "compress",
        created_at: "",
        updated_at: "",
      } as any)
      .mockResolvedValueOnce({
        id: "job-A",
        status: "done",
        media_type: "image",
        operation: "compress",
        created_at: "",
        updated_at: "",
      } as any)

    const { result } = renderHook(({ jobId }) => useJobPolling(jobId, 100), {
      initialProps: { jobId: "job-A" },
    })

    // Initially status is null or pending
    expect(result.current.status).toBeNull()

    // Wait for the hook to update and eventually receive 'done'
    await waitFor(() => {
      expect(result.current.status).toBe("done")
    })

    // Polling should have stopped, so getJobStatus shouldn't be called anymore
    const callCountAfterDone = mockGetJobStatus.mock.calls.length
    expect(callCountAfterDone).toBe(2)
  })

  it("should reactivate polling when jobId changes to a new job", async () => {
    const mockGetJobStatus = vi.mocked(getJobStatus)

    // Sequence of mock returns:
    // For job-A: returns "done" (stops polling)
    // For job-B: returns "processing" then "done"
    mockGetJobStatus
      .mockResolvedValueOnce({
        id: "job-A",
        status: "done",
        media_type: "image",
        operation: "compress",
        created_at: "",
        updated_at: "",
      } as any)
      .mockResolvedValueOnce({
        id: "job-B",
        status: "processing",
        media_type: "image",
        operation: "compress",
        created_at: "",
        updated_at: "",
      } as any)
      .mockResolvedValueOnce({
        id: "job-B",
        status: "done",
        media_type: "image",
        operation: "compress",
        created_at: "",
        updated_at: "",
      } as any)

    const { result, rerender } = renderHook(({ jobId }) => useJobPolling(jobId, 100), {
      initialProps: { jobId: "job-A" },
    })

    // Wait for job-A to complete and set active to false
    await waitFor(() => {
      expect(result.current.status).toBe("done")
    })

    // Now change the jobId to "job-B"
    rerender({ jobId: "job-B" })

    // It should immediately reset and start polling again, seeing "processing" then "done"
    await waitFor(() => {
      expect(result.current.status).toBe("done")
    })

    // Verify it called for job-B
    const calls = mockGetJobStatus.mock.calls
    expect(calls.length).toBe(3)
    expect(calls[0][0]).toBe("job-A")
    expect(calls[1][0]).toBe("job-B")
    expect(calls[2][0]).toBe("job-B")
  })
})
