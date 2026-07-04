import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { UploadDropzone } from "../UploadDropzoneNew"

describe("UploadDropzone", () => {
  it("renders dropzone text", () => {
    const onFileSelect = vi.fn()
    render(<UploadDropzone onFileSelect={onFileSelect} />)
    expect(screen.getByText(/Drop files here/i)).toBeInTheDocument()
  })

  it("calls onFileSelect when file is selected via input", () => {
    const onFileSelect = vi.fn()
    render(<UploadDropzone onFileSelect={onFileSelect} />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File(["content"], "test.txt", { type: "text/plain" })
    fireEvent.change(input, { target: { files: [file] } })
    expect(onFileSelect).toHaveBeenCalledWith(file)
  })
})