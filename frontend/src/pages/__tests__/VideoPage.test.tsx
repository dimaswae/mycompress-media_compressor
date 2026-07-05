import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { VideoPage } from "../VideoPage"
import { useFileUpload } from "../../hooks/useFileUpload"
import { useJobPolling } from "../../hooks/useJobPolling"
import { ToastProvider } from "../../components/common/ToastContext"

vi.mock("../../hooks/useFileUpload", () => ({ useFileUpload: vi.fn() }))
vi.mock("../../hooks/useJobPolling", () => ({ useJobPolling: vi.fn() }))
vi.mock("../../api/videoApi", () => ({
  compressVideo: vi.fn(),
  decompressVideo: vi.fn(),
  embedMessage: vi.fn(),
  extractMessage: vi.fn(),
  compareVideo: vi.fn(),
}))
vi.mock("../../components/upload/UploadDropzoneNew", () => ({
  UploadDropzone: ({ onFileSelect }: any) => (
    <button
      data-testid="mock-upload"
      onClick={() => onFileSelect(new File([""], "test.mp4", { type: "video/mp4" }))}
    >
      Select File
    </button>
  ),
}))

const defaultPolling = { status: null, job: null, error: null, stopPolling: vi.fn() }

function renderWithProviders(ui: React.ReactElement) {
  return render(<ToastProvider>{ui}</ToastProvider>)
}

describe("VideoPage", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useJobPolling).mockReturnValue(defaultPolling as any)
  })

  /* ── Mode selector ── */
  it("renders mode selector with Compress and Hide/Extract tabs", () => {
    vi.mocked(useFileUpload).mockReturnValue({ upload: vi.fn(), progress: 0, isUploading: false, error: null, result: null } as any)
    renderWithProviders(<VideoPage />)
    expect(screen.getByRole("tab", { name: /compress/i })).toBeInTheDocument()
    expect(screen.getByRole("tab", { name: /hide.*message/i })).toBeInTheDocument()
  })

  it("shows compress form by default", () => {
    vi.mocked(useFileUpload).mockReturnValue({ upload: vi.fn(), progress: 0, isUploading: false, error: null, result: null } as any)
    renderWithProviders(<VideoPage />)
    expect(screen.getByText(/compress video/i)).toBeInTheDocument()
    expect(screen.queryByText(/hide message/i)).not.toBeInTheDocument()
  })

  /* ── Compress mode ── */
  it("renders CRF slider in compress mode", () => {
    vi.mocked(useFileUpload).mockReturnValue({ upload: vi.fn(), progress: 0, isUploading: false, error: null, result: null } as any)
    renderWithProviders(<VideoPage />)
    expect(screen.getByRole("slider")).toBeInTheDocument()
  })

  it("shows progress bar when uploading", () => {
    vi.mocked(useFileUpload).mockReturnValue({ upload: vi.fn(), progress: 60, isUploading: true, error: null, result: null } as any)
    renderWithProviders(<VideoPage />)
    const bar = screen.getByRole("progressbar")
    expect(bar).toHaveAttribute("aria-valuenow", "60")
  })

  it("hides CRF slider in Decompress sub-mode", () => {
    vi.mocked(useFileUpload).mockReturnValue({ upload: vi.fn(), progress: 0, isUploading: false, error: null, result: null } as any)
    renderWithProviders(<VideoPage />)
    fireEvent.click(screen.getByText("Decompress"))
    expect(screen.queryByRole("slider")).not.toBeInTheDocument()
  })

  /* ── Stego mode ── */
  it("switches to stego mode and shows embed form", () => {
    vi.mocked(useFileUpload).mockReturnValue({ upload: vi.fn(), progress: 0, isUploading: false, error: null, result: null } as any)
    renderWithProviders(<VideoPage />)
    fireEvent.click(screen.getByRole("tab", { name: /hide.*message/i }))
    expect(screen.getByText(/hide message in video/i)).toBeInTheDocument()
    // CRF slider should be gone in stego mode
    expect(screen.queryByRole("slider")).not.toBeInTheDocument()
  })

  it("shows AES-256 Encryption in stego mode", () => {
    vi.mocked(useFileUpload).mockReturnValue({ upload: vi.fn(), progress: 0, isUploading: false, error: null, result: null } as any)
    renderWithProviders(<VideoPage />)
    fireEvent.click(screen.getByRole("tab", { name: /hide.*message/i }))
    expect(screen.getByText("AES-256 Encryption")).toBeInTheDocument()
  })

  it("shows I-frame steganography hint in stego mode", () => {
    vi.mocked(useFileUpload).mockReturnValue({ upload: vi.fn(), progress: 0, isUploading: false, error: null, result: null } as any)
    renderWithProviders(<VideoPage />)
    fireEvent.click(screen.getByRole("tab", { name: /hide.*message/i }))
    expect(screen.getByText(/I-frames/i)).toBeInTheDocument()
  })

  /* ── Friendly error ── */
  it("shows friendly error for unsupported format", () => {
    vi.mocked(useFileUpload).mockReturnValue({
      upload: vi.fn(), progress: 0, isUploading: false,
      error: "File content does not match expected signature for '.mp4'",
      result: null,
    } as any)
    renderWithProviders(<VideoPage />)
    expect(screen.getByRole("alert")).toHaveTextContent(/valid.*unmodified/i)
  })
})
