import { expect, vi } from "vitest"
import * as matchers from "@testing-library/jest-dom/matchers"
import "@testing-library/jest-dom"
import React from "react"

expect.extend(matchers)

// Mock react-router-dom so individual page tests don't fail due to missing Router context (e.g. from Link components)
vi.mock("react-router-dom", () => ({
  Link: ({ to, children, ...props }: any) => React.createElement("a", { href: to, ...props }, children),
  NavLink: ({ to, children, className, ...props }: any) => {
    const cls = typeof className === "function" ? className({ isActive: false }) : className
    return React.createElement("a", { href: to, className: cls, ...props }, children)
  },
  useNavigate: () => vi.fn(),
  useLocation: () => ({ pathname: "/" }),
}))