import { colors, radius } from "../styles";

interface TagGroupProps {
  label: string;
  options: string[];
  value: string;
  onChange: (v: string) => void;
}

export default function TagGroup({ label, options, value, onChange }: TagGroupProps) {
  return (
    <div style={{ marginBottom: "16px" }}>
      <label style={{ display: "block", fontSize: "13px", fontWeight: 500, color: colors.fgSecondary, marginBottom: "6px" }}>{label}</label>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
        {options.map((opt) => (
          <button
            key={opt}
            onClick={() => onChange(opt)}
            style={value === opt
              ? { padding: "6px 14px", border: `1px solid ${colors.accent}`, borderRadius: "20px", fontSize: "13px", cursor: "pointer", background: colors.accent, color: "#fff" }
              : { padding: "6px 14px", border: `1px solid ${colors.border}`, borderRadius: "20px", fontSize: "13px", cursor: "pointer", background: "transparent", color: colors.muted }
            }
          >
            {opt}
          </button>
        ))}
      </div>
    </div>
  );
}
