import { describe, it, expect, vi, beforeEach } from "vitest"
import { embedMessage } from "../videoApi"
import * as client from "../client"

vi.mock("../client", () => ({
  fetchApi: vi.fn(),
  uploadApi: vi.fn(),
}))

describe("videoApi", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("embedMessage calls uploadApi and triggers onProgress callback", async () => {
    const mockFile = new File([""], "video.mp4", { type: "video/mp4" })
    const onProgress = vi.fn()

    // Simulate uploadApi triggering progress
    vi.mocked(client.uploadApi).mockImplementation(async (_endpoint, _form, progressCb) => {
      if (progressCb) {
        progressCb(15)
        progressCb(60)
        progressCb(100)
      }
      return { job_id: "test-video-job" }
    })

    const result = await embedMessage(mockFile, "test message", "password", onProgress)

    expect(client.uploadApi).toHaveBeenCalledWith(
      "/video/embed",
      expect.any(FormData),
      onProgress
    )
    expect(onProgress).toHaveBeenCalledWith(15)
    expect(onProgress).toHaveBeenCalledWith(60)
    expect(onProgress).toHaveBeenCalledWith(100)
    expect(result).toEqual({ job_id: "test-video-job" })
  })
})
