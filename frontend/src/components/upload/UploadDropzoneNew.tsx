import React, { useCallback, useRef, useState } from "react";

interface UploadDropzoneProps {
  onFileSelect: (file: File) => void;
  accept?: string;
  selectedFileName?: string | null;
}

export function UploadDropzone({
  onFileSelect,
  accept = "*",
  selectedFileName,
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
      aria-label="Upload file — click or drag and drop"
      onKeyDown={handleKey}
      onClick={open}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`dropzone${isDrag ? " drag-over" : ""}`}
      style={{ outline: "none" }}
    >
      {selectedFileName ? (
        <>
          <div style={{
            width: "2.5rem", height: "2.5rem", borderRadius: "50%",
            background: "rgba(34,197,94,0.15)", border: "1px solid rgba(34,197,94,0.3)",
            display: "flex", alignItems: "center", justifyContent: "center",
            color: "var(--color-primary)", marginBottom: "0.75rem",
          }}>
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M20 6L9 17l-5-5" /></svg>
          </div>
          <p style={{ fontWeight: 600, color: "var(--color-text)", marginBottom: "0.25rem", fontSize: "0.9375rem" }}>
            {selectedFileName}
          </p>
          <p style={{ color: "var(--color-muted)", fontSize: "0.8125rem", margin: 0 }}>
            Click to change file
          </p>
        </>
      ) : (
        <>
          <div style={{
            width: "2.5rem", height: "2.5rem", borderRadius: "50%",
            background: "var(--color-surface-2)", border: "1px solid var(--color-border)",
            display: "flex", alignItems: "center", justifyContent: "center",
            color: "var(--color-muted)", marginBottom: "0.875rem",
          }}>
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          </div>
          <p style={{ fontWeight: 600, color: "var(--color-text)", marginBottom: "0.25rem", fontSize: "0.9375rem" }}>
            Drop your file here
          </p>
          <p style={{ color: "var(--color-muted)", fontSize: "0.8125rem", margin: 0 }}>
            or <span style={{ color: "var(--color-primary)", fontWeight: 600 }}>click to browse</span>
          </p>
        </>
      )}
      <input
        ref={inputRef}
        id="file-input"
        type="file"
        style={{ display: "none" }}
        accept={accept}
        onChange={handleChange}
      />
    </div>
  );
}
