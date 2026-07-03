import { createBrowserRouter, RouterProvider } from "react-router-dom"
import { HomePage } from "./pages/HomePage"
import { ImagePage } from "./pages/ImagePage"
import { AudioPage } from "./pages/AudioPage"
import { VideoPage } from "./pages/VideoPage"
import { JobHistoryPage } from "./pages/JobHistoryPage"

const router = createBrowserRouter([
  {
    path: "/",
    element: <HomePage />,
  },
  {
    path: "/image",
    element: <ImagePage />,
  },
  {
    path: "/audio",
    element: <AudioPage />,
  },
  {
    path: "/video",
    element: <VideoPage />,
  },
  {
    path: "/jobs",
    element: <JobHistoryPage />,
  },
])

export function AppRouter() {
  return <RouterProvider router={router} />
}