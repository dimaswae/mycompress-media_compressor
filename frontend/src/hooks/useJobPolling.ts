import { useEffect, useState } from "react"
import { getJobStatus } from "../api/jobsApi"
import type { JobStatusResponse } from "../types/job"

export function useJobPolling(
  jobId: string,
  intervalMs: number = 2000
): {
  status: string | null
  job: JobStatusResponse | null
  error: string | null
  stopPolling: () => void
} {
  const [status, setStatus] = useState<string | null>(null)
  const [job, setJob] = useState<JobStatusResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [active, setActive] = useState(true)

  useEffect(() => {
    setActive(true)
    setStatus(null)
    setJob(null)
    setError(null)
  }, [jobId])

  useEffect(() => {
    if (!active || !jobId) return

    const poll = async () => {
      try {
        const j = await getJobStatus(jobId)
        setJob(j)
        setStatus(j.status)
        if (j.status === "done" || j.status === "failed") {
          setActive(false)
        }
      } catch (e) {
        setError((e as Error).message)
        setActive(false)
      }
    }

    poll()
    const timer = setInterval(poll, intervalMs)
    return () => clearInterval(timer)
  }, [jobId, active, intervalMs])

  const stopPolling = () => setActive(false)

  return { status, job, error, stopPolling }
}