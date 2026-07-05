import React from "react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
  isLoading?: boolean;
}

export function Button({
  children,
  variant = "primary",
  isLoading,
  disabled,
  style,
  ...props
}: ButtonProps) {
  const variantStyle: React.CSSProperties =
    variant === "primary"
      ? { background: "var(--color-primary)", color: "#0F172A" }
      : variant === "ghost"
        ? { background: "transparent", color: "var(--color-muted)", border: "1px solid var(--color-border)" }
        : { background: "var(--color-surface-2)", color: "var(--color-text)", border: "1px solid var(--color-border)" }

  return (
    <button
      className="btn"
      disabled={isLoading || disabled}
      style={{
        ...variantStyle,
        opacity: isLoading || disabled ? 0.5 : 1,
        cursor: isLoading || disabled ? "not-allowed" : "pointer",
        ...style,
      }}
      onMouseEnter={(e) => {
        if (!disabled && !isLoading && variant === "primary") {
          const el = e.currentTarget
          el.style.background = "var(--color-primary-h)"
          el.style.boxShadow = "0 0 16px var(--color-primary-glow)"
          el.style.transform = "translateY(-1px)"
        }
      }}
      onMouseLeave={(e) => {
        if (!disabled && !isLoading && variant === "primary") {
          const el = e.currentTarget
          el.style.background = "var(--color-primary)"
          el.style.boxShadow = "none"
          el.style.transform = "translateY(0)"
        }
      }}
      {...props}
    >
      {isLoading && <span className="spinner" aria-hidden />}
      <span>{isLoading ? "Processing..." : children}</span>
    </button>
  );
}
