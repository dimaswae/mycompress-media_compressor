import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { JobStatusBadge } from "../JobStatusBadge"

describe("JobStatusBadge", () => {
  it("renders done status", () => {
    render(<JobStatusBadge status="done" />)
    expect(screen.getByText("done")).toBeInTheDocument()
    // Design token class: badge-done (not bg-green-600)
    expect(screen.getByText("done").className).toContain("badge-done")
  })

  it("renders processing status with running badge class", () => {
    render(<JobStatusBadge status="processing" />)
    expect(screen.getByText("processing")).toBeInTheDocument()
    expect(screen.getByText("processing").className).toContain("badge-running")
  })

  it("renders failed status with failed badge class", () => {
    render(<JobStatusBadge status="failed" />)
    expect(screen.getByText("failed")).toBeInTheDocument()
    expect(screen.getByText("failed").className).toContain("badge-failed")
  })

  it("renders pending status with pending badge class", () => {
    render(<JobStatusBadge status="pending" />)
    expect(screen.getByText("pending").className).toContain("badge-pending")
  })
})