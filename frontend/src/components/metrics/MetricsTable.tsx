interface MetricsTableProps {
  metrics: Record<string, number>
}

export function MetricsTable({ metrics }: MetricsTableProps) {
  return (
    <table className="w-full text-left border-collapse">
      <tbody>
        {Object.entries(metrics).map(([key, value]) => (
          <tr key={key} className="border-b border-gray-700">
            <td className="py-2 pr-4 text-gray-400">{key}</td>
            <td className="py-2 text-white">
              {typeof value === "number" ? value.toFixed(4) : String(value)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}