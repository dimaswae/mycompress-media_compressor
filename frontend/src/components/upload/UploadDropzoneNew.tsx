import React, { useCallback, useRef, useState } from "react";

interface UploadDropzoneProps {
  onFileSelect: (file: File) => void;
  accept?: string;
}

export function UploadDropzone({
  onFileSelect,
  accept = "*",
}: UploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isDrag, setIsDrag] = useState(false);

  const open = () => inputRef.current?.click();

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      open();
    }
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDrag(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDrag(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDrag(false);
      const file = e.dataTransfer.files[0];
      if (file) onFileSelect(file);
    },
    [onFileSelect],
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) onFileSelect(file);
    },
    [onFileSelect],
  );

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label="Upload file"
      onKeyDown={handleKey}
      onClick={open}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`cursor-pointer rounded-lg border-2 p-6 text-center focus:outline-none focus-visible:ring-2 ${isDrag ? "border-blue-400 bg-gray-800" : "border-gray-600"}`}
    >
      <p className="text-gray-300">Drop files here or press Enter to choose</p>
      <input
        ref={inputRef}
        id="file-input"
        type="file"
        className="sr-only"
        accept={accept}
        onChange={handleChange}
      />
    </div>
  );
}
