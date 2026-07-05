import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { UploadDropzone } from "../UploadDropzoneNew"

describe("UploadDropzone", () => {
  it("renders dropzone with 'Drop your file here' prompt", () => {
    const onFileSelect = vi.fn()
    render(<UploadDropzone onFileSelect={onFileSelect} />)
    expect(screen.getByText(/Drop your file here/i)).toBeInTheDocument()
    expect(screen.getByText(/click to browse/i)).toBeInTheDocument()
  })

  it("shows selected filename when selectedFileName prop is provided", () => {
    const onFileSelect = vi.fn()
    render(<UploadDropzone onFileSelect={onFileSelect} selectedFileName="photo.png" />)
    expect(screen.getByText("photo.png")).toBeInTheDocument()
    expect(screen.getByText(/click to change file/i)).toBeInTheDocument()
  })

  it("calls onFileSelect when file is selected via input", () => {
    const onFileSelect = vi.fn()
    render(<UploadDropzone onFileSelect={onFileSelect} />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File(["content"], "test.txt", { type: "text/plain" })
    fireEvent.change(input, { target: { files: [file] } })
    expect(onFileSelect).toHaveBeenCalledWith(file)
  })

  it("is keyboard accessible with role=button", () => {
    const onFileSelect = vi.fn()
    render(<UploadDropzone onFileSelect={onFileSelect} />)
    expect(screen.getByRole("button", { name: /upload file/i })).toBeInTheDocument()
  })
})