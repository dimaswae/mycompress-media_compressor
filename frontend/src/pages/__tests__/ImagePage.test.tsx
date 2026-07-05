import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { ImagePage } from "../ImagePage"
import { useJobPolling } from "../../hooks/useJobPolling"
import { useFileUpload } from "../../hooks/useFileUpload"
import * as imageApi from "../../api/imageApi"

// Mock hooks and APIs
vi.mock("../../hooks/useFileUpload", () => ({
  useFileUpload: vi.fn(),
}))

vi.mock("../../hooks/useJobPolling", () => ({
  useJobPolling: vi.fn(),
}))

vi.mock("../../api/imageApi", () => ({
  embedMessage: vi.fn(),
  compareImage: vi.fn(),
}))

vi.mock("../../components/common/ToastContext", () => ({
  useToast: () => ({
    showToast: vi.fn(),
  }),
}))

// Mock child components to make testing state changes easy
vi.mock("../../components/upload/UploadDropzoneNew", () => ({
  UploadDropzone: ({ onFileSelect }: any) => (
    <button
      data-testid="mock-upload"
      onClick={() => onFileSelect(new File([""], "test.png", { type: "image/png" }))}
    >
      Select File
    </button>
  ),
}))

describe("ImagePage", () => {
  beforeEach(() => {
    vi.clearAllMocks()

    // Default mock implementation for useJobPolling
    vi.mocked(useJobPolling).mockReturnValue({
      status: null,
      job: null,
      error: null,
      stopPolling: vi.fn(),
    })

    // Default mock implementation for useFileUpload
    vi.mocked(useFileUpload).mockReturnValue({
      upload: vi.fn(async (cb) => cb()),
      progress: 0,
      isUploading: false,
      error: null,
      result: null,
    } as any)
  })

  it("renders upload page correctly", () => {
    render(<ImagePage />)
    expect(screen.getByText("Image Processing")).toBeInTheDocument()
    expect(screen.getByText("Embed Message")).toBeInTheDocument()
  })

  it("calculates image capacity dynamically based on image dimensions", async () => {
    const originalImage = globalThis.Image
    class MockImage {
      onload: (() => void) | null = null
      onerror: (() => void) | null = null
      _src: string = ""
      width: number = 300
      height: number = 200

      get src() {
        return this._src
      }

      set src(val: string) {
        this._src = val
        setTimeout(() => {
          if (this.onload) this.onload()
        }, 0)
      }
    }
    globalThis.Image = MockImage as any

    globalThis.URL.createObjectURL = vi.fn(() => "blob:http://localhost/test-uuid")
    globalThis.URL.revokeObjectURL = vi.fn()

    render(<ImagePage />)

    fireEvent.click(screen.getByTestId("mock-upload"))

    await waitFor(() => {
      expect(screen.getByText("Message capacity: 22496 bytes")).toBeInTheDocument()
    })

    // Now enable encryption: checkbox toggle
    // It should subtract 44 bytes -> 22496 - 44 = 22452 bytes.
    const encryptCheckbox = screen.getByRole("switch")
    fireEvent.click(encryptCheckbox)

    await waitFor(() => {
      expect(screen.getByText("Message capacity: 22452 bytes")).toBeInTheDocument()
    })

    // Toggle encryption off: should go back to 22496 bytes
    fireEvent.click(encryptCheckbox)

    await waitFor(() => {
      expect(screen.getByText("Message capacity: 22496 bytes")).toBeInTheDocument()
    })

    globalThis.Image = originalImage
  })

  it("shows ResultPanel with download link and size summary when job is done", async () => {
    const mockUpload = vi.fn(async (cb) => {
      await cb()
      return { job_id: "test-job-id" }
    })
    vi.mocked(useFileUpload).mockReturnValue({
      upload: mockUpload,
      progress: 0,
      isUploading: false,
      error: null,
      result: null,
    } as any)

    vi.mocked(useJobPolling).mockImplementation((jobId: string) => {
      if (jobId === "test-job-id") {
        return {
          status: "done",
          job: {
            job_id: "test-job-id",
            status: "done",
            media_type: "image",
            operation: "embed",
            created_at: "",
            updated_at: "",
          },
          error: null,
          stopPolling: vi.fn(),
        }
      }
      return { status: null, job: null, error: null, stopPolling: vi.fn() }
    })

    const mockCompareResponse = {
      job_id: "test-job-id",
      original_size: 2000,
      result_size: 1500,
      metrics: { psnr: 50.1, ssim: 0.995, mse: 0.5 },
      original_url: "/api/v1/jobs/test-job-id/download/original",
      result_url: "/api/v1/jobs/test-job-id/download",
    }
    vi.mocked(imageApi.compareImage).mockResolvedValue(mockCompareResponse)
    vi.mocked(imageApi.embedMessage).mockResolvedValue({
      job_id: "test-job-id",
      status: "processing",
      metrics: {},
    })

    globalThis.URL.createObjectURL = vi.fn(() => "blob:http://localhost/test-uuid")
    globalThis.URL.revokeObjectURL = vi.fn()

    render(<ImagePage />)

    // Select file and submit
    fireEvent.click(screen.getByTestId("mock-upload"))
    fireEvent.click(screen.getByText("Embed Message"))

    // Wait for compareImage to be called (compare data loaded)
    await waitFor(() => {
      expect(imageApi.compareImage).toHaveBeenCalledWith("test-job-id")
    })

    // ── ResultPanel assertions ──
    // 1. Download link must be present and point to the correct endpoint
    const downloadLink = screen.getByRole("link", { name: /download result/i })
    expect(downloadLink).toBeInTheDocument()
    expect(downloadLink).toHaveAttribute("href", expect.stringContaining("/jobs/test-job-id/download"))

    // 2. Size summary: original → result sizes should be visible
    // 2.0 KB → 1.5 KB
    expect(screen.getByText("1.95 KB")).toBeInTheDocument() // 2000 B
    expect(screen.getByText("1.46 KB")).toBeInTheDocument() // 1500 B

    // 3. Collapsible technical details trigger should be rendered
    expect(screen.getByText(/technical details/i)).toBeInTheDocument()
  })
})
