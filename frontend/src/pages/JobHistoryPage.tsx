import { useEffect, useState } from "react"
import { JobStatusBadge } from "../components/jobs/JobStatusBadge"
import * as jobsApi from "../api/jobsApi"
import type { JobStatusResponse } from "../types/job"

export function JobHistoryPage() {
  const [jobs, setJobs] = useState<JobStatusResponse[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    jobsApi.listJobs().then(setJobs).finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <p className="text-gray-400">Loading jobs...</p>
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-4">Job History</h1>

      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="border-b border-gray-700">
            <th className="pb-2 text-gray-400">ID</th>
            <th className="pb-2 text-gray-400">Type</th>
            <th className="pb-2 text-gray-400">Operation</th>
            <th className="pb-2 text-gray-400">Status</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr key={job.job_id} className="border-b border-gray-700">
              <td className="py-2 text-white">{job.job_id.slice(0, 8)}...</td>
              <td className="py-2 text-gray-400">{job.media_type || "-"}</td>
              <td className="py-2 text-gray-400">{job.operation}</td>
              <td className="py-2">
                <JobStatusBadge status={job.status as any} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}