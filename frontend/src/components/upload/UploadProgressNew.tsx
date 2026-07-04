import React from "react";

interface UploadProgressProps {
  percent: number;
}

export function UploadProgress({ percent }: UploadProgressProps) {
  const pct = Math.max(0, Math.min(100, Math.round(percent)));
  return (
    <div
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={pct}
      className="h-4 w-full rounded-full bg-gray-700"
    >
      <div
        className="h-4 rounded-full bg-gradient-to-r from-blue-500 to-teal-400 transition-all"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}
