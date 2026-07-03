import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { JobStatusBadge } from "../JobStatusBadge"

describe("JobStatusBadge", () => {
  it("renders done status with green color", () => {
    render(<JobStatusBadge status="done" />)
    expect(screen.getByText("done")).toBeInTheDocument()
    expect(screen.getByText("done").className).toContain("bg-green-600")
  })

  it("renders processing status with yellow color", () => {
    render(<JobStatusBadge status="processing" />)
    expect(screen.getByText("processing").className).toContain("bg-yellow-600")
  })

  it("renders failed status with red color", () => {
    render(<JobStatusBadge status="failed" />)
    expect(screen.getByText("failed").className).toContain("bg-red-600")
  })
})