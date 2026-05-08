import { colorsDark } from "../styles";

/** Single centralized <style> tag with all global keyframe animations and dark theme CSS vars */
export default function GlobalAnimations() {
  const d = colorsDark;
  return (
    <style>{`
      @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      @keyframes blink { 0%,100% { opacity:1; } 50% { opacity:0; } }
      @keyframes streamPulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
      @keyframes progressGlow { 0% { box-shadow: 0 0 4px ${d.primary}; } 50% { box-shadow: 0 0 12px ${d.primary}; } 100% { box-shadow: 0 0 4px ${d.primary}; } }

      :root {
        --bg: #FAF6F1; --bg-warm: #F5EDE3; --surface: #FFFCF8; --surface-raised: #FFFFFF;
        --fg: #2C2420; --fg-secondary: #5C4E44; --muted: #8C7E72; --muted-light: #B8AEA4;
        --border: #E8E0D8; --border-light: #F0EAE2;
        --accent: #B85C3A; --accent-hover: #A04E30; --accent-bg: oklch(92% 0.04 45);
        --primary: #6B8E5A; --primary-hover: #5A7A4A;
        --success: #6B8E5A; --warning: #C4943A; --danger: #B84A3A; --info: #5A7E8E;
        --primary-muted: rgba(107,142,90,0.12); --primary-border: rgba(107,142,90,0.25);
        --danger-bg: rgba(184,74,58,0.12); --danger-border: rgba(184,74,58,0.25); --danger-muted: rgba(184,74,58,0.12);
        --warning-bg: rgba(196,148,58,0.12); --warning-border: rgba(196,148,58,0.25); --warning-muted: rgba(196,148,58,0.12);
        --info-muted: rgba(90,126,142,0.12); --info-border: rgba(90,126,142,0.25);
        --success-muted: rgba(107,142,90,0.12); --success-border: rgba(107,142,90,0.25);
      }

      [data-theme="dark"] {
        --bg: ${d.bg}; --bg-warm: ${d.bgWarm}; --surface: ${d.surface}; --surface-raised: ${d.surfaceRaised};
        --fg: ${d.fg}; --fg-secondary: ${d.fgSecondary}; --muted: ${d.muted}; --muted-light: ${d.mutedLight};
        --border: ${d.border}; --border-light: ${d.borderLight};
        --accent: ${d.accent}; --accent-hover: ${d.accentHover}; --accent-bg: ${d.accentBg};
        --primary: ${d.primary}; --primary-hover: ${d.primaryHover};
        --success: ${d.success}; --warning: ${d.warning}; --danger: ${d.danger}; --info: ${d.info};
        --primary-muted: ${d.primaryMuted}; --primary-border: ${d.primaryBorder};
        --danger-bg: ${d.dangerBg}; --danger-border: ${d.dangerBorder}; --danger-muted: ${d.dangerMuted};
        --warning-bg: ${d.warningBg}; --warning-border: ${d.warningBorder}; --warning-muted: ${d.warningMuted};
        --info-muted: ${d.infoMuted}; --info-border: ${d.infoBorder};
        --success-muted: ${d.successMuted}; --success-border: ${d.successBorder};
      }

      /* Dark mode global overrides for inline-styled elements */
      [data-theme="dark"] input:not([type]),
      [data-theme="dark"] input[type="text"],
      [data-theme="dark"] input[type="number"],
      [data-theme="dark"] input[type="password"],
      [data-theme="dark"] textarea,
      [data-theme="dark"] select {
        background: ${d.surface} !important;
        color: ${d.fg} !important;
        border-color: ${d.border} !important;
      }
      [data-theme="dark"] button[style*="background: transparent"],
      [data-theme="dark"] button[style*="background:transparent"] {
        color: ${d.fgSecondary} !important;
      }
    `}</style>
  );
}
