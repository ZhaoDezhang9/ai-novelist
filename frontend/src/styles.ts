import React from "react";

// ========== Font Families ==========
export const fonts = {
  display: "'Noto Serif SC','Songti SC','STSong',Georgia,serif",
  body: "'Noto Sans SC','PingFang SC','Microsoft YaHei',system-ui,sans-serif",
  mono: "'JetBrains Mono','IBM Plex Mono',ui-monospace,monospace",
};

// ========== Color Tokens ==========
export const colors = {
  // Backgrounds (warm, paper-like)
  bg: "#FAF6F1",
  bgWarm: "#F5EDE3",
  surface: "#FFFCF8",
  surfaceRaised: "#FFFFFF",
  // Text
  fg: "#2C2420",
  fgSecondary: "#5C4E44",
  muted: "#8C7E72",
  mutedLight: "#B8AEA4",
  // Borders
  border: "#E8E0D8",
  borderLight: "#F0EAE2",
  // Accent
  accent: "#B85C3A",
  accentHover: "#A04E30",
  accentBg: "oklch(92% 0.04 45)",
  // Semantic
  success: "#6B8E5A",
  successMuted: "rgba(107, 142, 90, 0.12)",
  successBorder: "rgba(107, 142, 90, 0.25)",
  warning: "#C4943A",
  warningMuted: "rgba(196, 148, 58, 0.12)",
  warningBorder: "rgba(196, 148, 58, 0.25)",
  danger: "#B84A3A",
  dangerMuted: "rgba(184, 74, 58, 0.12)",
  dangerBorder: "rgba(184, 74, 58, 0.25)",
  info: "#5A7E8E",
  infoMuted: "rgba(90, 126, 142, 0.12)",
  infoBorder: "rgba(90, 126, 142, 0.25)",
  // Primary (green for actions)
  primary: "#6B8E5A",
  primaryHover: "#5A7A4A",
  primaryMuted: "rgba(107, 142, 90, 0.12)",
  primaryBorder: "rgba(107, 142, 90, 0.25)",
  // Aliases for backward compatibility
  textMuted: "#8C7E72",
  textDim: "#B8AEA4",
  textSecondary: "#5C4E44",
  text: "#2C2420",
  dangerBg: "rgba(184, 74, 58, 0.12)",
  bgElevated: "#FFFFFF",
  warningBg: "rgba(196, 148, 58, 0.12)",
};

// ========== Dark Theme Colors ==========
export const colorsDark = {
  // Backgrounds
  bg: "#1A1714",
  bgWarm: "#201D19",
  surface: "#262220",
  surfaceRaised: "#2E2A27",
  // Text
  fg: "#E8E0D8",
  fgSecondary: "#C4B8AC",
  muted: "#8C7E72",
  mutedLight: "#5C5248",
  // Borders
  border: "#3A3430",
  borderLight: "#2E2A27",
  // Accent
  accent: "#D4795E",
  accentHover: "#E08A6F",
  accentBg: "oklch(28% 0.04 45)",
  // Semantic
  success: "#8CB67A",
  successMuted: "rgba(140, 182, 122, 0.12)",
  successBorder: "rgba(140, 182, 122, 0.25)",
  warning: "#D4A84A",
  warningMuted: "rgba(212, 168, 74, 0.12)",
  warningBorder: "rgba(212, 168, 74, 0.25)",
  danger: "#D46A5A",
  dangerMuted: "rgba(212, 106, 90, 0.12)",
  dangerBorder: "rgba(212, 106, 90, 0.25)",
  info: "#7AA0B0",
  infoMuted: "rgba(122, 160, 176, 0.12)",
  infoBorder: "rgba(122, 160, 176, 0.25)",
  // Primary (green for actions)
  primary: "#8CB67A",
  primaryHover: "#9DC68C",
  primaryMuted: "rgba(140, 182, 122, 0.12)",
  primaryBorder: "rgba(140, 182, 122, 0.25)",
  // Aliases for backward compatibility
  textMuted: "#8C7E72",
  textDim: "#5C5248",
  textSecondary: "#C4B8AC",
  text: "#E8E0D8",
  dangerBg: "rgba(212, 106, 90, 0.12)",
  bgElevated: "#2E2A27",
  warningBg: "rgba(212, 168, 74, 0.12)",
};

// ========== Genre Colors ==========
export const genreColors: Record<string, string> = {
  xiuxian: "#6B8E5A",
  xuanhui: "#8B5CF6",
  dushi: "#3B82F6",
  kehuan: "#06B6D4",
  lingyi: "#EC4899",
  junshi: "#92400E",
  lishi: "#B45309",
  wuxia: "#059669",
  youxi: "#7C3AED",
  tiyu: "#DC2626",
  qihuan: "#D946EF",
  "仙侠": "#6B8E5A",
  "玄幻": "#8B5CF6",
  "都市": "#3B82F6",
  "科幻": "#06B6D4",
  "灵异": "#EC4899",
  "军事": "#92400E",
  "历史": "#B45309",
  "武侠": "#059669",
  "游戏": "#7C3AED",
  "体育": "#DC2626",
  "奇幻": "#D946EF",
  "言情": "#F43F5E",
  "悬疑": "#8B5CF6",
  "其他": "#8C7E72",
};

// ========== Genre Gradients ==========
export const genreGradients: Record<string, { from: string; to: string }> = {
  "仙侠": { from: "#6B8E5A", to: "#059669" },
  "玄幻": { from: "#8B5CF6", to: "#06B6D4" },
  "都市": { from: "#3B82F6", to: "#6B8E5A" },
  "科幻": { from: "#06B6D4", to: "#3B82F6" },
  "言情": { from: "#EC4899", to: "#F43F5E" },
  "悬疑": { from: "#8B5CF6", to: "#2C2420" },
  "历史": { from: "#B45309", to: "#C4943A" },
  "武侠": { from: "#059669", to: "#6B8E5A" },
  "游戏": { from: "#7C3AED", to: "#8B5CF6" },
  "奇幻": { from: "#D946EF", to: "#8B5CF6" },
  "其他": { from: "#8C7E72", to: "#B8AEA4" },
};

// ========== Shadow & Radius ==========
export const shadows = {
  card: "0 1px 3px rgba(44,36,32,.06),0 4px 12px rgba(44,36,32,.04)",
  hover: "0 2px 8px rgba(44,36,32,.1),0 8px 24px rgba(44,36,32,.06)",
};

export const radius = {
  sm: "6px",
  md: "10px",
  lg: "14px",
};

// ========== Spacing Scale ==========
export const space = {
  1: 4, 2: 8, 3: 12, 4: 16, 5: 20, 6: 24, 8: 32, 10: 40, 12: 48, 16: 64,
} as const;

// ========== Typography ==========
export const font = {
  xs: { fontSize: "11px", lineHeight: "16px" },
  sm: { fontSize: "13px", lineHeight: "18px" },
  base: { fontSize: "14px", lineHeight: "20px" },
  md: { fontSize: "15px", lineHeight: "22px" },
  lg: { fontSize: "16px", lineHeight: "24px" },
  xl: { fontSize: "18px", lineHeight: "28px" },
  "2xl": { fontSize: "22px", lineHeight: "30px" },
  "3xl": { fontSize: "28px", lineHeight: "36px" },
} as const;

// ========== Breakpoints ==========
export const bp = {
  sm: "@media (max-width: 640px)",
  md: "@media (max-width: 868px)",
  lg: "@media (max-width: 1100px)",
} as const;

// ========== Layout ==========
export const layout: Record<string, React.CSSProperties> = {
  page: { maxWidth: "1200px", margin: "0 auto", padding: space[6] },
  centered: { display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: space[16], color: colors.muted },
  sidebar: { width: "260px", flexShrink: 0, borderRight: `1px solid ${colors.border}`, background: colors.bgWarm, height: "100vh", position: "sticky", top: 0, overflow: "auto" },
  main: { flex: 1, minWidth: 0 },
};

// ========== Buttons ==========
const btnBase: React.CSSProperties = {
  display: "inline-flex", alignItems: "center", justifyContent: "center", gap: space[2],
  padding: `${space[2]} ${space[4]}`, fontSize: "13px", fontWeight: 600, fontFamily: "inherit",
  border: "none", borderRadius: radius.md, cursor: "pointer", transition: "all 0.15s ease",
  outline: "none",
};

export const btn: Record<string, React.CSSProperties> = {
  primary: { ...btnBase, background: colors.primary, color: "#fff" },
  primaryGhost: { ...btnBase, background: "transparent", color: colors.primary, border: `1px solid ${colors.primaryBorder}` },
  danger: { ...btnBase, background: colors.danger, color: "#fff" },
  warning: { ...btnBase, background: colors.warning, color: "#fff" },
  ghost: { ...btnBase, background: "transparent", color: colors.fgSecondary, border: `1px solid ${colors.border}` },
  icon: { ...btnBase, padding: space[2], borderRadius: radius.sm, background: "transparent", color: colors.muted },
  tag: { ...btnBase, padding: `${space[1]} ${space[3]}`, fontSize: "12px", borderRadius: radius.sm, fontWeight: 500 },
  tagActive: { background: colors.primaryMuted, color: colors.primary, border: `1px solid ${colors.primaryBorder}` },
  tagInactive: { background: "transparent", color: colors.muted, border: `1px solid ${colors.border}` },
};

// ========== Inputs ==========
export const input: React.CSSProperties = {
  width: "100%", padding: `${space[3]} ${space[3]}`, fontSize: "14px", fontFamily: "inherit",
  background: colors.surface, border: `1px solid ${colors.border}`, borderRadius: radius.md,
  color: colors.fg, outline: "none", transition: "border-color 0.15s",
};

export const textarea: React.CSSProperties = {
  ...input, resize: "vertical", minHeight: "80px", lineHeight: "1.6",
};

export const label: React.CSSProperties = {
  display: "block", fontSize: "12px", fontWeight: 600, color: colors.fgSecondary,
  marginBottom: space[2], letterSpacing: "0.02em", textTransform: "uppercase",
};

// ========== Cards ==========
export const card: React.CSSProperties = {
  background: colors.surface, border: `1px solid ${colors.border}`,
  borderRadius: radius.md, padding: `${space[4]} ${space[5]}`,
  transition: "border-color 0.15s, background 0.15s",
  boxShadow: shadows.card,
};

export const cardInteractive: React.CSSProperties = {
  ...card, cursor: "pointer",
};

// ========== Status Badges ==========
export const badge: Record<string, React.CSSProperties> = {
  base: { display: "inline-flex", alignItems: "center", padding: `${2}px ${space[2]}`, fontSize: "11px", fontWeight: 600, borderRadius: radius.sm, letterSpacing: "0.02em" },
  success: { background: colors.successMuted, color: colors.success, border: `1px solid ${colors.successBorder}` },
  danger: { background: colors.dangerMuted, color: colors.danger, border: `1px solid ${colors.dangerBorder}` },
  warning: { background: colors.warningMuted, color: colors.warning, border: `1px solid ${colors.warningBorder}` },
  info: { background: colors.infoMuted, color: colors.info, border: `1px solid ${colors.infoBorder}` },
  muted: { background: colors.surface, color: colors.muted, border: `1px solid ${colors.border}` },
};

// ========== Scrollbar ==========
export const scrollbar: React.CSSProperties = {
  scrollbarWidth: "thin", scrollbarColor: `${colors.border} transparent`,
};

// ========== Section ==========
export const section: Record<string, React.CSSProperties> = {
  title: { ...font.lg, fontWeight: 700, color: colors.fg, marginBottom: space[4] },
  subtitle: { ...font.sm, color: colors.muted, marginTop: -space[3], marginBottom: space[5] },
  divider: { border: "none", borderTop: `1px solid ${colors.border}`, margin: `${space[6]} 0` },
};
