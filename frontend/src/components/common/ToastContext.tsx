import React, { createContext, useContext, useState, useCallback } from "react";
import { Toast } from "./Toast";

type ToastEntry = {
  id: string;
  message: string;
  type?: "info" | "success" | "error";
};

const ToastContext = createContext<
  | { showToast: (message: string, type?: ToastEntry["type"]) => void }
  | undefined
>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastEntry[]>([]);

  const showToast = useCallback(
    (message: string, type: ToastEntry["type"] = "info") => {
      const id = String(Date.now()) + Math.random().toString(36).slice(2, 7);
      const entry: ToastEntry = { id, message, type };
      setToasts((s) => [...s, entry]);
      setTimeout(() => setToasts((s) => s.filter((t) => t.id !== id)), 5000);
    },
    [],
  );

  const remove = (id: string) => setToasts((s) => s.filter((t) => t.id !== id));

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="fixed right-6 bottom-6 z-50 flex flex-col gap-3">
        {toasts.map((t) => (
          <div key={t.id} onClick={() => remove(t.id)}>
            <Toast
              message={t.message}
              type={t.type}
              onClose={() => remove(t.id)}
            />
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
