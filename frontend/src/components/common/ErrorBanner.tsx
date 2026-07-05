interface ErrorBannerProps {
  message: string
}

export function ErrorBanner({ message }: ErrorBannerProps) {
  return (
    <div className="bg-red-900 border border-red-700 text-red-200 px-4 py-3 rounded">
      <p>{message}</p>
    </div>
  )
}