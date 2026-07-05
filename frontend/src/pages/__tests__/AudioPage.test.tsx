import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { AudioPage } from "../AudioPage"
import { useFileUpload } from "../../hooks/useFileUpload"
import { useJobPolling } from "../../hooks/useJobPolling"
import { ToastProvider } from "../../components/common/ToastContext"

vi.mock("../../hooks/useFileUpload", () => ({ useFileUpload: vi.fn() }))
vi.mock("../../hooks/useJobPolling", () => ({ useJobPolling: vi.fn() }))
vi.mock("../../api/audioApi", () => ({
  compressAudio: vi.fn(),
  decompressAudio: vi.fn(),
  embedMessage: vi.fn(),
  extractMessage: vi.fn(),
  compareAudio: vi.fn(),
}))
vi.mock("../../components/upload/UploadDropzoneNew", () => ({
  UploadDropzone: ({ onFileSelect }: any) => (
    <button
      data-testid="mock-upload"
      onClick={() => onFileSelect(new File([""], "test.wav", { type: "audio/wav" }))}
    >
      Select File
    </button>
  ),
}))

const defaultPolling = { status: null, job: null, error: null, stopPolling: vi.fn() }

function renderWithProviders(ui: React.ReactElement) {
  return render(<ToastProvider>{ui}</ToastProvider>)
}

describe("AudioPage", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useJobPolling).mockReturnValue(defaultPolling as any)
    // Some tests click the upload dropzone which triggers URL.createObjectURL in other pages;
    // add stubs here as a safety net to avoid unhandled errors
    globalThis.URL.createObjectURL = vi.fn(() => "blob:test")
    globalThis.URL.revokeObjectURL = vi.fn()
  })

  /* ── Mode selector ── */
  it("renders mode selector with Compress and Hide/Extract tabs", () => {
    vi.mocked(useFileUpload).mockReturnValue({ upload: vi.fn(), progress: 0, isUploading: false, error: null, result: null } as any)
    renderWithProviders(<AudioPage />)
    expect(screen.getByRole("tab", { name: /compress/i })).toBeInTheDocument()
    expect(screen.getByRole("tab", { name: /hide.*message/i })).toBeInTheDocument()
  })

  it("shows compress form by default (Compress to MP3 button visible)", () => {
    vi.mocked(useFileUpload).mockReturnValue({ upload: vi.fn(), progress: 0, isUploading: false, error: null, result: null } as any)
    renderWithProviders(<AudioPage />)
    // Use getByRole to avoid ambiguity with paragraph text "compress to MP3"
    expect(screen.getByRole("button", { name: /compress to mp3/i })).toBeInTheDocument()
    expect(screen.queryByText("AES-256 Encryption")).not.toBeInTheDocument()
  })

  /* ── Compress mode ── */
  it("shows bitrate options in compress mode", () => {
    vi.mocked(useFileUpload).mockReturnValue({ upload: vi.fn(), progress: 0, isUploading: false, error: null, result: null } as any)
    renderWithProviders(<AudioPage />)
    expect(screen.getByText("128k")).toBeInTheDocument()
    expect(screen.getByText("320k")).toBeInTheDocument()
  })

  it("shows progress bar when uploading", () => {
    vi.mocked(useFileUpload).mockReturnValue({ upload: vi.fn(), progress: 45, isUploading: true, error: null, result: null } as any)
    renderWithProviders(<AudioPage />)
    const bar = screen.getByRole("progressbar")
    expect(bar).toHaveAttribute("aria-valuenow", "45")
  })

  /* ── Stego mode ── */
  it("switches to stego mode and shows AES-256 Encryption toggle", () => {
    vi.mocked(useFileUpload).mockReturnValue({ upload: vi.fn(), progress: 0, isUploading: false, error: null, result: null } as any)
    renderWithProviders(<AudioPage />)
    fireEvent.click(screen.getByRole("tab", { name: /hide.*message/i }))
    expect(screen.getByText("AES-256 Encryption")).toBeInTheDocument()
  })

  it("shows WAV-only hint in stego mode", () => {
    vi.mocked(useFileUpload).mockReturnValue({ upload: vi.fn(), progress: 0, isUploading: false, error: null, result: null } as any)
    renderWithProviders(<AudioPage />)
    fireEvent.click(screen.getByRole("tab", { name: /hide.*message/i }))
    // "LSB embedding" is a direct text node in the hint paragraph (not inside a <strong>),
    // so getNodeText() can match it reliably even though "WAV" is wrapped in <strong>.
    expect(screen.getByText(/LSB embedding/i)).toBeInTheDocument()
  })

  it("shows friendly error when WAV is required but wrong format given", () => {
    vi.mocked(useFileUpload).mockReturnValue({
      upload: vi.fn(), progress: 0, isUploading: false,
      error: "Only WAV files are supported for audio steganography",
      result: null,
    } as any)
    renderWithProviders(<AudioPage />)
    fireEvent.click(screen.getByRole("tab", { name: /hide.*message/i }))
    expect(screen.getByRole("alert")).toHaveTextContent(/WAV.*file/i)
  })
})
