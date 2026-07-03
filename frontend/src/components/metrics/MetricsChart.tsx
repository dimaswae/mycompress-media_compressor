import React from "react"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts"

interface MetricsChartProps {
  metrics: Record<string, number>
  dataKey?: string
}

export function MetricsChart({ metrics, dataKey = "value" }: MetricsChartProps) {
  const data = Object.entries(metrics)
    .filter(([key]) => key.includes("ratio") || key.includes("time"))
    .map(([key, value]) => ({ name: key, value }))

  if (data.length === 0) {
    return <p className="text-gray-400">No chartable metrics available</p>
  }

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <XAxis dataKey="name" stroke="#9ca3af" />
          <YAxis stroke="#9ca3af" />
          <Tooltip />
          <Bar dataKey={dataKey} fill="#3b82f6" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}