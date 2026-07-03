import React from "react"

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary"
  isLoading?: boolean
}

export function Button({
  children,
  variant = "primary",
  isLoading,
  className = "",
  ...props
}: ButtonProps) {
  const baseClasses =
    "px-4 py-2 rounded font-medium transition-colors disabled:opacity-50"
  const primaryClasses = "bg-blue-600 hover:bg-blue-700 text-white"
  const secondaryClasses = "bg-gray-600 hover:bg-gray-700 text-white"

  return (
    <button
      className={`${baseClasses} ${variant === "primary" ? primaryClasses : secondaryClasses} ${className}`}
      disabled={isLoading || props.disabled}
      {...props}
    >
      {isLoading ? "Loading..." : children}
    </button>
  )
}