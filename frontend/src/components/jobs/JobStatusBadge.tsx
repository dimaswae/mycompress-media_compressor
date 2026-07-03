import React from "react"

type Status = "pending" | "processing" | "done" | "failed" | "deleted"

interface JobStatusBadgeProps {
  status: Status
}

const statusColors: Record<Status, string> = {
  pending: "bg-gray-600 text-gray-200",
  processing: "bg-yellow-600 text-yellow-100",
  done: "bg-green-600 text-green-100",
  failed: "bg-red-600 text-red-100",
  deleted: "bg-gray-800 text-gray-400",
}

export function JobStatusBadge({ status }: JobStatusBadgeProps) {
  return (
    <span
      className={`px-2 py-1 text-xs rounded ${statusColors[status] || statusColors.pending}`}
    >
      {status}
    </span>
  )
}