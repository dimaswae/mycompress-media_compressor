interface MessageInputProps {
  value: string
  onChange: (value: string) => void
  maxLength?: number
}

export function MessageInput({
  value,
  onChange,
  maxLength = 1000,
}: MessageInputProps) {
  return (
    <div className="flex flex-col gap-2">
      <textarea
        className="w-full bg-gray-800 border border-gray-600 rounded p-2 text-white"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Enter secret message..."
        rows={4}
      />
      <span className="text-sm text-gray-400 self-end">
        {value.length} / {maxLength}
      </span>
    </div>
  )
}