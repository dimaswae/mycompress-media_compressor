import React, { useState } from "react"

interface EncryptionToggleProps {
  onPasswordChange: (password: string) => void
  isEnabled: boolean
  onToggle: (enabled: boolean) => void
}

export function EncryptionToggle({
  onPasswordChange,
  isEnabled,
  onToggle,
}: EncryptionToggleProps) {
  const [password, setPassword] = useState("")

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newPassword = e.target.value
    setPassword(newPassword)
    onPasswordChange(newPassword)
  }

  return (
    <div className="flex flex-col gap-2">
      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={isEnabled}
          onChange={(e) => onToggle(e.target.checked)}
          className="w-4 h-4"
        />
        <span className="text-white">Enable AES Encryption</span>
      </label>
      {isEnabled && (
        <input
          type="password"
          className="w-full bg-gray-800 border border-gray-600 rounded p-2 text-white"
          value={password}
          onChange={handlePasswordChange}
          placeholder="Enter encryption password"
        />
      )}
    </div>
  )
}