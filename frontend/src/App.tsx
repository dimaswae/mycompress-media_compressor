import { AppRouter } from "./router";
import { ToastProvider } from "./components/common/ToastContext";

export default function App() {
  return (
    <ToastProvider>
      <div className="min-h-screen bg-gray-950 text-white">
        <header className="border-b border-gray-800 bg-gray-900">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
            <h1 className="text-lg font-bold">mycompress</h1>
            <nav className="space-x-3">
              <a href="/" className="text-gray-300 hover:text-white">
                Home
              </a>
              <a href="/jobs" className="text-gray-300 hover:text-white">
                Jobs
              </a>
            </nav>
          </div>
        </header>

        <main className="mx-auto max-w-6xl p-4">
          <AppRouter />
        </main>
      </div>
    </ToastProvider>
  );
}
