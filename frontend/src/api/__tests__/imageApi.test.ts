import { describe, it, expect, vi, beforeEach } from "vitest"
import { compareImage } from "../imageApi"

describe("imageApi - compareImage", () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it("should return the CompareResponse with correct fields", async () => {
    const mockResponse = {
      job_id: "test-job-123",
      original_size: 1024,
      result_size: 512,
      metrics: {
        psnr: 45.2,
        ssim: 0.98,
        mse: 1.2,
      },
    }

    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    } as Response)

    const result = await compareImage("test-job-123")

    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining("/image/test-job-123/compare"),
      undefined
    )
    expect(result).toEqual(mockResponse)
    expect(result.original_size).toBe(1024)
    expect(result.result_size).toBe(512)
    expect(result.metrics.psnr).toBe(45.2)
  })
})
