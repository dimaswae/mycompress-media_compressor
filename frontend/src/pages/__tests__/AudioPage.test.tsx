import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen } from "@testing-library/react"
import { AudioPage } from "../AudioPage"
import { useFileUpload } from "../../hooks/useFileUpload"
import { useJobPolling } from "../../hooks/useJobPolling"

// Mock hooks and APIs
vi.mock("../../hooks/useFileUpload", () => ({
  useFileUpload: vi.fn(),
}))

vi.mock("../../hooks/useJobPolling", () => ({
  useJobPolling: vi.fn(),
}))

vi.mock("../../api/audioApi", () => ({
  embedMessage: vi.fn(),
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

describe("AudioPage", () => {
  beforeEach(() => {
    vi.clearAllMocks()

    vi.mocked(useJobPolling).mockReturnValue({
      status: null,
      job: null,
      error: null,
      stopPolling: vi.fn(),
    } as any)
  })

  it("renders upload page and shows progress bar when uploading", () => {
    // Mock useFileUpload returning progress 45% and uploading
    vi.mocked(useFileUpload).mockReturnValue({
      upload: vi.fn(),
      progress: 45,
      isUploading: true,
      error: null,
      result: null,
    } as any)

    render(<AudioPage />)

    expect(screen.getByText("Audio Processing")).toBeInTheDocument()

    // Verify progress bar is rendered and shows progress percent
    const progressbar = screen.getByRole("progressbar")
    expect(progressbar).toBeInTheDocument()
    expect(progressbar).toHaveAttribute("aria-valuenow", "45")
  })
})
