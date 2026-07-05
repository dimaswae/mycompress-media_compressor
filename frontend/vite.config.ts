/// <reference types="vitest" />
import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

// Conditionally set `base` for GitHub Pages deployment.
// Set VITE_GH_PAGES_BASE=/mycompress-media_compressor/ in .env.production
// to enable GH Pages subpath. Local dev (`npm run dev`) always uses "/".
export default defineConfig(() => {
  // @ts-ignore
  const base = (typeof process !== "undefined" && process?.env?.VITE_GH_PAGES_BASE) || "/"

  return {
    base,
    plugins: [react(), tailwindcss()],
    server: {
      port: 5173,
      proxy: {
        "/api": {
          target: "http://localhost:8000",
          changeOrigin: true,
        },
      },
    },
    test: {
      environment: "jsdom",
      globals: true,
      setupFiles: ["./src/test-setup.ts"],
    },
  }
})
