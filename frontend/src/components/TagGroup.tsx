interface TagGroupProps {
  label: string;
  options: string[];
  value: string;
  onChange: (v: string) => void;
}

export default function TagGroup({ label, options, value, onChange }: TagGroupProps) {
  return (
    <div style={{ marginBottom: "16px" }}>
      <label style={{ display: "block", fontSize: "13px", fontWeight: 500, color: "#5C4E44", marginBottom: "6px" }}>{label}</label>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
        {options.map((opt) => (
          <button
            key={opt}
            onClick={() => onChange(opt)}
            style={value === opt
              ? { padding: "6px 14px", border: "1px solid #B85C3A", borderRadius: "20px", fontSize: "13px", cursor: "pointer", background: "#B85C3A", color: "#fff" }
              : { padding: "6px 14px", border: "1px solid #E8E0D8", borderRadius: "20px", fontSize: "13px", cursor: "pointer", background: "transparent", color: "#8C7E72" }
            }
          >
            {opt}
          </button>
        ))}
      </div>
    </div>
  );
}
