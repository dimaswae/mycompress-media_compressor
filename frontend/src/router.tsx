import { createBrowserRouter, RouterProvider, NavLink, Outlet } from "react-router-dom"
import { HomePage } from "./pages/HomePage"
import { ImagePage } from "./pages/ImagePage"
import { AudioPage } from "./pages/AudioPage"
import { VideoPage } from "./pages/VideoPage"
import { JobHistoryPage } from "./pages/JobHistoryPage"

// eslint-disable-next-line react-refresh/only-export-components
function Navbar() {
  return (
    <header
      style={{
        position: "fixed",
        top: "1rem",
        left: "1rem",
        right: "1rem",
        zIndex: 50,
        background: "rgba(15,23,42,0.85)",
        backdropFilter: "blur(16px)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-lg)",
        padding: "0.625rem 1.25rem",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        boxShadow: "0 4px 24px rgba(0,0,0,0.4)",
      }}
    >
      {/* Logo */}
      <a
        href="/"
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.5rem",
          textDecoration: "none",
        }}
      >
        <span
          style={{
            width: "1.75rem",
            height: "1.75rem",
            background: "linear-gradient(135deg,#22c55e,#38bdf8)",
            borderRadius: "0.5rem",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          <svg viewBox="0 0 24 24" fill="none" width="14" height="14" stroke="#0F172A" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
        </span>
        <span style={{ fontWeight: 800, fontSize: "1.0625rem", color: "var(--color-text)", letterSpacing: "-0.02em" }}>
          my<span style={{ color: "var(--color-primary)" }}>compress</span>
        </span>
      </a>

      {/* Nav links */}
      <nav style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
        {[
          { to: "/", label: "Home", exact: true },
          { to: "/image", label: "Image" },
          { to: "/audio", label: "Audio" },
          { to: "/video", label: "Video" },
          { to: "/jobs", label: "Jobs" },
        ].map(({ to, label, exact }) => (
          <NavLink
            key={to}
            to={to}
            end={exact}
            className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
          >
            {label}
          </NavLink>
        ))}
      </nav>
    </header>
  )
}

// Root layout: Navbar + page outlet — semua di dalam RouterProvider
// sehingga NavLink selalu punya Router context.
function AppLayout() {
  return (
    <div style={{ minHeight: "100vh", background: "var(--color-bg)" }}>
      <Navbar />
      <main style={{ paddingTop: "5.5rem" }}>
        <Outlet />
      </main>
    </div>
  )
}

const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { path: "/", element: <HomePage /> },
      { path: "/image", element: <ImagePage /> },
      { path: "/audio", element: <AudioPage /> },
      { path: "/video", element: <VideoPage /> },
      { path: "/jobs", element: <JobHistoryPage /> },
    ],
  },
])

export function AppRouter() {
  return <RouterProvider router={router} />
}