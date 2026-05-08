import { colors, space, font, radius, shadows } from "../styles";

interface ConfirmDialogProps {
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  danger?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmDialog({
  title, message, confirmLabel = "确认", cancelLabel = "取消",
  danger = false, onConfirm, onCancel,
}: ConfirmDialogProps) {
  return (
    <div onClick={onCancel} style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.35)",
      display: "flex", alignItems: "center", justifyContent: "center",
      zIndex: 9999, animation: "fadeIn 0.15s ease",
    }}>
      <div onClick={(e) => e.stopPropagation()} style={{
        background: colors.surfaceRaised, borderRadius: radius.lg,
        padding: space[6], maxWidth: 400, width: "90%",
        boxShadow: shadows.hover,
      }}>
        <h3 style={{ ...font.lg, fontWeight: 700, marginBottom: space[2], color: colors.fg }}>{title}</h3>
        <p style={{ ...font.sm, color: colors.fgSecondary, marginBottom: space[5], lineHeight: 1.6 }}>{message}</p>
        <div style={{ display: "flex", gap: space[3], justifyContent: "flex-end" }}>
          <button onClick={onCancel} style={{
            padding: `${space[2]} ${space[4]}`, borderRadius: radius.sm, fontSize: "13px",
            border: `1px solid ${colors.border}`, background: "transparent",
            color: colors.fgSecondary, cursor: "pointer",
          }}>{cancelLabel}</button>
          <button onClick={onConfirm} style={{
            padding: `${space[2]} ${space[4]}`, borderRadius: radius.sm, fontSize: "13px",
            border: "none", fontWeight: 600, cursor: "pointer",
            background: danger ? colors.danger : colors.primary,
            color: "#fff",
          }}>{confirmLabel}</button>
        </div>
      </div>
      <style>{`@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }`}</style>
    </div>
  );
}
