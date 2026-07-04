import { useCallback, useState } from "react"

export function useFileUpload() {
  const [progress, setProgress] = useState<number>(0)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<any>(null)
  const [isUploading, setIsUploading] = useState(false)

  const upload = useCallback(async (uploadFn: (onProgress: (p: number) => void) => Promise<any>) => {
    setIsUploading(true)
    setError(null)
    setProgress(0)
    setResult(null)

    try {
      const res = await uploadFn((p: number) => {
        setProgress(p)
      })
      setProgress(100)
      setResult(res)
      return res
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setIsUploading(false)
    }
  }, [])

  return { progress, error, result, isUploading, upload }
}