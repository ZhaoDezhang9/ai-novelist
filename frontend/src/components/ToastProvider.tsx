import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import { colors, space, font } from "../styles";

interface Toast {
  id: number;
  message: string;
  type: "success" | "error" | "info";
}

interface ToastContextType {
  toasts: Toast[];
  show: (message: string, type?: "success" | "error" | "info") => void;
}

const ToastContext = createContext<ToastContextType | null>(null);

let nextId = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const show = useCallback((message: string, type: "success" | "error" | "info" = "info") => {
    const id = nextId++;
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 3500);
  }, []);

  const bg = { success: colors.successMuted, error: colors.dangerMuted, info: colors.infoMuted };
  const border = { success: colors.successBorder, error: colors.dangerBorder, info: colors.infoBorder };
  const fg = { success: colors.success, error: colors.danger, info: colors.info };

  return (
    <ToastContext.Provider value={{ toasts, show }}>
      {children}
      <div style={{ position: "fixed", top: 20, right: 20, zIndex: 9999, display: "flex", flexDirection: "column", gap: 8 }}>
        {toasts.map((t) => (
          <div key={t.id} style={{
            padding: `${space[3]} ${space[4]}`, borderRadius: "8px", fontSize: "13px",
            background: bg[t.type], color: fg[t.type],
            border: `1px solid ${border[t.type]}`,
            animation: "toastIn 0.25s ease",
            maxWidth: 360, wordBreak: "break-word",
          }}>
            {t.message}
          </div>
        ))}
      </div>
      <style>{`@keyframes toastIn { from { opacity: 0; transform: translateX(20px); } to { opacity: 1; transform: translateX(0); } }`}</style>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
