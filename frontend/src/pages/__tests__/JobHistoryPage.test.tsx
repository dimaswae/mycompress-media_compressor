import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import { JobHistoryPage } from "../JobHistoryPage"
import * as jobsApi from "../../api/jobsApi"

vi.mock("../../api/jobsApi", () => ({
  listJobs: vi.fn(),
}))

describe("JobHistoryPage", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("renders a list of jobs with media_type and operation", async () => {
    const mockListJobs = vi.mocked(jobsApi.listJobs)
    mockListJobs.mockResolvedValue([
      {
        job_id: "job-12345678",
        status: "done",
        media_type: "image",
        operation: "compress",
        created_at: "2026-07-05T00:00:00Z",
        updated_at: "2026-07-05T00:01:00Z",
      },
      {
        job_id: "job-87654321",
        status: "failed",
        media_type: "audio",
        operation: "embed",
        created_at: "2026-07-05T00:02:00Z",
        updated_at: "2026-07-05T00:03:00Z",
      },
    ])

    render(<JobHistoryPage />)

    // Verify loading text is shown initially
    expect(screen.getByText("Loading jobs...")).toBeInTheDocument()

    // Wait for the jobs list to render
    await waitFor(() => {
      expect(screen.queryByText("Loading jobs...")).not.toBeInTheDocument()
    })

    // Verify headings
    expect(screen.getByText("ID")).toBeInTheDocument()
    expect(screen.getByText("Type")).toBeInTheDocument()
    expect(screen.getByText("Operation")).toBeInTheDocument()
    expect(screen.getByText("Status")).toBeInTheDocument()

    // Verify first job row
    expect(screen.getByText("job-1234...")).toBeInTheDocument()
    expect(screen.getByText("image")).toBeInTheDocument()
    expect(screen.getByText("compress")).toBeInTheDocument()

    // Verify second job row
    expect(screen.getByText("job-8765...")).toBeInTheDocument()
    expect(screen.getByText("audio")).toBeInTheDocument()
    expect(screen.getByText("embed")).toBeInTheDocument()
  })
})
