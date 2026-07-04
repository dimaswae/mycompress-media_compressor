import React from "react";

interface ToastProps {
  message: string;
  type?: "info" | "success" | "error";
  onClose?: () => void;
}

export function Toast({ message, type = "info", onClose }: ToastProps) {
  const bg =
    type === "error"
      ? "bg-red-700"
      : type === "success"
        ? "bg-green-700"
        : "bg-black/80";

  return (
    <div
      role="status"
      aria-live="polite"
      className={`${bg} rounded px-4 py-2 text-white shadow`}
    >
      <div className="flex items-center gap-3">
        <div className="flex-1">{message}</div>
        <button
          onClick={onClose}
          aria-label="Close toast"
          className="opacity-80 hover:opacity-100"
        >
          ✕
        </button>
      </div>
    </div>
  );
}
