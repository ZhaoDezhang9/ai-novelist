import { colors, colorsDark } from "../styles";

/** Single centralized <style> tag with all global keyframe animations and dark theme CSS vars */
export default function GlobalAnimations() {
  return (
    <style>{`
      @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      @keyframes blink { 0%,100% { opacity:1; } 50% { opacity:0; } }
      @keyframes streamPulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
      @keyframes progressGlow { 0% { box-shadow: 0 0 4px ${colors.primary}; } 50% { box-shadow: 0 0 12px ${colors.primary}; } 100% { box-shadow: 0 0 4px ${colors.primary}; } }
      [data-theme="dark"] {
        --bg: #1A1714; --bg-warm: #201D19; --surface: #262220; --surface-raised: #2E2A27;
        --fg: #E8E0D8; --fg-secondary: #C4B8AC; --muted: #8C7E72; --border: #3A3430;
        --accent: #D4795E; --accent-hover: #E08A6F; --accent-bg: oklch(28% 0.04 45);
        --primary: #8CB67A; --primary-hover: #9DC68C; --success: #8CB67A;
        --warning: #D4A84A; --danger: #D46A5A; --info: #7AA0B0;
      }
    `}</style>
  );
}
