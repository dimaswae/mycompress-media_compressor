import { describe, it, expect, vi, beforeEach } from "vitest"
import { embedMessage } from "../audioApi"
import * as client from "../client"

vi.mock("../client", () => ({
  fetchApi: vi.fn(),
  uploadApi: vi.fn(),
}))

describe("audioApi", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("embedMessage calls uploadApi and triggers onProgress callback", async () => {
    const mockFile = new File([""], "audio.wav", { type: "audio/wav" })
    const onProgress = vi.fn()

    // Simulate uploadApi triggering progress
    vi.mocked(client.uploadApi).mockImplementation(async (_endpoint, _form, progressCb) => {
      if (progressCb) {
        progressCb(25)
        progressCb(75)
        progressCb(100)
      }
      return { job_id: "test-audio-job" }
    })

    const result = await embedMessage(mockFile, "test message", "password", onProgress)

    expect(client.uploadApi).toHaveBeenCalledWith(
      "/audio/embed",
      expect.any(FormData),
      onProgress
    )
    expect(onProgress).toHaveBeenCalledWith(25)
    expect(onProgress).toHaveBeenCalledWith(75)
    expect(onProgress).toHaveBeenCalledWith(100)
    expect(result).toEqual({ job_id: "test-audio-job" })
  })
})
