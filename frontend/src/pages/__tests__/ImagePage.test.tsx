import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { ImagePage } from "../ImagePage"
import { useJobPolling } from "../../hooks/useJobPolling"
import { useFileUpload } from "../../hooks/useFileUpload"
import * as imageApi from "../../api/imageApi"

vi.mock("../../hooks/useFileUpload", () => ({ useFileUpload: vi.fn() }))
vi.mock("../../hooks/useJobPolling", () => ({ useJobPolling: vi.fn() }))
vi.mock("../../api/imageApi", () => ({
  compressImage: vi.fn(),
  decompressImage: vi.fn(),
  embedMessage: vi.fn(),
  extractMessage: vi.fn(),
  compareImage: vi.fn(),
}))
vi.mock("../../components/common/ToastContext", () => ({
  useToast: () => ({ showToast: vi.fn() }),
}))
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

const defaultPolling = { status: null, job: null, error: null, stopPolling: vi.fn() }
const defaultUpload = { upload: vi.fn(async (cb: any) => cb()), progress: 0, isUploading: false, error: null, result: null }

describe("ImagePage", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useJobPolling).mockReturnValue(defaultPolling as any)
    vi.mocked(useFileUpload).mockReturnValue(defaultUpload as any)
    // Required by handleFileSelect → URL.createObjectURL(file)
    globalThis.URL.createObjectURL = vi.fn(() => "blob:test")
    globalThis.URL.revokeObjectURL = vi.fn()
  })

  /* ── Mode selector ── */
  it("renders mode selector with both tabs", () => {
    render(<ImagePage />)
    expect(screen.getByRole("tab", { name: /compress/i })).toBeInTheDocument()
    expect(screen.getByRole("tab", { name: /hide.*message/i })).toBeInTheDocument()
  })

  it("shows compress form by default (compress tab active)", () => {
    render(<ImagePage />)
    expect(screen.getByText("Compress Image")).toBeInTheDocument()
    // "2. Secret Message" section title only appears in stego mode, not compress mode
    expect(screen.queryByText("2. Secret Message")).not.toBeInTheDocument()
  })

  it("switches to stego mode when Hide/Extract tab is clicked", () => {
    render(<ImagePage />)
    fireEvent.click(screen.getByRole("tab", { name: /hide.*message/i }))
    expect(screen.getByText(/hide message in image/i)).toBeInTheDocument()
    expect(screen.queryByText("Compress Image")).not.toBeInTheDocument()
  })

  /* ── Compress mode ── */
  it("renders sub-mode toggle (Compress / Decompress) in compress mode", () => {
    render(<ImagePage />)
    expect(screen.getByText("Compress")).toBeInTheDocument()
    expect(screen.getByText("Decompress")).toBeInTheDocument()
  })

  it("shows RLE and Huffman algorithm options in compress mode", () => {
    render(<ImagePage />)
    expect(screen.getByText("RLE")).toBeInTheDocument()
    expect(screen.getByText("Huffman")).toBeInTheDocument()
  })

  it("calls compressImage on submit in compress mode", async () => {
    vi.mocked(imageApi.compressImage).mockResolvedValue({ job_id: "j1", status: "processing", metrics: {} })
    vi.mocked(useFileUpload).mockReturnValue({
      upload: vi.fn(async (cb: any) => { await cb(vi.fn()); return { job_id: "j1", status: "processing", metrics: {} } }),
      progress: 0, isUploading: false, error: null, result: null,
    } as any)
    render(<ImagePage />)
    fireEvent.click(screen.getByTestId("mock-upload"))
    fireEvent.click(screen.getByText("Compress Image"))
    await waitFor(() => expect(vi.mocked(useFileUpload)().upload).toHaveBeenCalled())
  })

  /* ── Stego mode ── */
  it("shows capacity indicator after selecting a file in stego mode", async () => {
    const originalImage = globalThis.Image
    class MockImage {
      onload: (() => void) | null = null; onerror: (() => void) | null = null
      _src = ""; width = 300; height = 200
      get src() { return this._src }
      set src(val: string) { this._src = val; setTimeout(() => { if (this.onload) this.onload() }, 0) }
    }
    globalThis.Image = MockImage as any
    globalThis.URL.createObjectURL = vi.fn(() => "blob:test")
    globalThis.URL.revokeObjectURL = vi.fn()

    render(<ImagePage />)
    fireEvent.click(screen.getByRole("tab", { name: /hide.*message/i }))
    fireEvent.click(screen.getByTestId("mock-upload"))

    await waitFor(() => {
      expect(screen.getByText("Message capacity: 22496 bytes")).toBeInTheDocument()
    })
    globalThis.Image = originalImage
  })

  it("disables Hide Message button when message input is empty", () => {
    render(<ImagePage />)
    fireEvent.click(screen.getByRole("tab", { name: /hide.*message/i }))
    fireEvent.click(screen.getByTestId("mock-upload"))
    const btn = screen.getByText(/hide message in image/i).closest("button")!
    expect(btn).toBeDisabled()
  })

  it("shows compress-text-message section (not image compress) in stego mode", () => {
    render(<ImagePage />)
    fireEvent.click(screen.getByRole("tab", { name: /hide.*message/i }))
    // Section title must clarify this compresses the message TEXT, not the image
    expect(screen.getByText(/compress hidden message.*optional/i)).toBeInTheDocument()
  })

  /* ── Result panel ── */
  it("shows ResultPanel download link when job is done (compress mode)", async () => {
    vi.mocked(useJobPolling).mockReturnValue({
      status: "done",
      job: { job_id: "j1", status: "done", media_type: "image", operation: "compress", created_at: "", updated_at: "" },
      error: null, stopPolling: vi.fn(),
    } as any)
    vi.mocked(imageApi.compareImage).mockResolvedValue({
      job_id: "j1", original_size: 5000, result_size: 3000,
      metrics: { psnr: 40 }, original_url: "/api/v1/jobs/j1/download/original", result_url: "/api/v1/jobs/j1/download",
    })
    vi.mocked(useFileUpload).mockReturnValue({
      upload: vi.fn(async (cb: any) => { await cb(vi.fn()); return { job_id: "j1", status: "done", metrics: {} } }),
      progress: 0, isUploading: false, error: null, result: null,
    } as any)

    render(<ImagePage />)
    fireEvent.click(screen.getByTestId("mock-upload"))
    fireEvent.click(screen.getByText("Compress Image"))

    await waitFor(() => {
      const link = screen.getByRole("link", { name: /download result/i })
      expect(link).toHaveAttribute("href", expect.stringContaining("/jobs/j1/download"))
    })
  })

  /* ── Friendly error ── */
  it("shows friendly error when backend returns unsupported extension", () => {
    vi.mocked(useFileUpload).mockReturnValue({
      ...defaultUpload,
      error: "Unsupported extension '.cmp'. Allowed: ...",
    } as any)
    render(<ImagePage />)
    expect(screen.getByRole("alert")).toHaveTextContent(/not supported.*PNG or JPG/i)
  })

  /* ── Progress bar ── */
  it("shows progress bar while uploading", () => {
    vi.mocked(useFileUpload).mockReturnValue({
      upload: vi.fn(), progress: 55, isUploading: true, error: null, result: null,
    } as any)
    render(<ImagePage />)
    const bar = screen.getByRole("progressbar")
    expect(bar).toHaveAttribute("aria-valuenow", "55")
  })
})
