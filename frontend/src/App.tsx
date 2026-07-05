import { ToastProvider } from "./components/common/ToastContext"
import { AppRouter } from "./router"

export default function App() {
  return (
    <ToastProvider>
      <AppRouter />
    </ToastProvider>
  )
}
