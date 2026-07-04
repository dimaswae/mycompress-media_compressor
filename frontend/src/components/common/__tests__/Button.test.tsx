import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { Button } from "../Button"

describe("Button", () => {
  it("renders children", () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText("Click me")).toBeInTheDocument()
  })

  it("shows loading text when isLoading", () => {
    render(<Button isLoading>Click me</Button>)
    expect(screen.getByText("Loading...")).toBeInTheDocument()
  })

  it("calls onClick when clicked", () => {
    const onClick = vi.fn()
    render(<Button onClick={onClick}>Click</Button>)
    fireEvent.click(screen.getByText("Click"))
    expect(onClick).toHaveBeenCalled()
  })

  it("applies primary classes by default", () => {
    const { container } = render(<Button>Primary</Button>)
    expect(container.querySelector("button")?.className).toContain("bg-blue-600")
  })
})