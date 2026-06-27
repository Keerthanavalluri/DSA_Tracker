"use client";

import React, { createContext, useContext, useState, useCallback, useRef } from "react";

export type ToastType = "success" | "error" | "info" | "warning";

export interface Toast {
  id: string;
  type: ToastType;
  message: string;
}

interface ToastContextValue {
  toasts: Toast[];
  toast: (message: string, type?: ToastType) => void;
  dismiss: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue>({
  toasts: [],
  toast: () => {},
  dismiss: () => {},
});

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const timers = useRef<Record<string, ReturnType<typeof setTimeout>>>({});

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
    clearTimeout(timers.current[id]);
    delete timers.current[id];
  }, []);

  const toast = useCallback(
    (message: string, type: ToastType = "info") => {
      const id = Math.random().toString(36).slice(2);
      setToasts((prev) => [...prev.slice(-4), { id, type, message }]);
      timers.current[id] = setTimeout(() => dismiss(id), 4000);
    },
    [dismiss]
  );

  return (
    <ToastContext.Provider value={{ toasts, toast, dismiss }}>
      {children}
      <ToastContainer toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  );
}

export const useToast = () => useContext(ToastContext);

const ICONS: Record<ToastType, string> = {
  success: "✓",
  error: "✕",
  warning: "⚠",
  info: "ℹ",
};

const COLORS: Record<ToastType, string> = {
  success: "#10b981",
  error: "#ef4444",
  warning: "#f59e0b",
  info: "#6366f1",
};

function ToastContainer({
  toasts,
  onDismiss,
}: {
  toasts: Toast[];
  onDismiss: (id: string) => void;
}) {
  return (
    <div
      style={{
        position: "fixed",
        bottom: "1.5rem",
        right: "1.5rem",
        zIndex: 9999,
        display: "flex",
        flexDirection: "column",
        gap: "0.75rem",
        pointerEvents: "none",
      }}
    >
      {toasts.map((t) => (
        <div
          key={t.id}
          onClick={() => onDismiss(t.id)}
          style={{
            pointerEvents: "auto",
            display: "flex",
            alignItems: "center",
            gap: "0.75rem",
            padding: "0.875rem 1.25rem",
            background: "rgba(15, 23, 42, 0.95)",
            border: `1px solid ${COLORS[t.type]}44`,
            borderLeft: `4px solid ${COLORS[t.type]}`,
            borderRadius: "10px",
            boxShadow: `0 8px 32px rgba(0,0,0,0.4), 0 0 12px ${COLORS[t.type]}22`,
            backdropFilter: "blur(12px)",
            minWidth: "280px",
            maxWidth: "380px",
            cursor: "pointer",
            animation: "toastIn 0.3s ease-out",
          }}
        >
          <span
            style={{
              width: "22px",
              height: "22px",
              borderRadius: "50%",
              background: `${COLORS[t.type]}22`,
              color: COLORS[t.type],
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "0.8rem",
              fontWeight: "bold",
              flexShrink: 0,
            }}
          >
            {ICONS[t.type]}
          </span>
          <span style={{ fontSize: "0.875rem", lineHeight: 1.4, flex: 1 }}>
            {t.message}
          </span>
          <span style={{ opacity: 0.4, fontSize: "0.75rem", flexShrink: 0 }}>✕</span>
        </div>
      ))}
      <style>{`
        @keyframes toastIn {
          from { opacity: 0; transform: translateX(20px) scale(0.96); }
          to   { opacity: 1; transform: translateX(0) scale(1); }
        }
      `}</style>
    </div>
  );
}
