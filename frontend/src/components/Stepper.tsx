interface StepperProps {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
  step?: number;
}

export default function Stepper({ label, value, onChange, min = 1, max = 999, step = 1 }: StepperProps) {
  return (
    <div style={{ marginBottom: "16px" }}>
      <label style={{ display: "block", fontSize: "13px", fontWeight: 500, color: "#5C4E44", marginBottom: "6px" }}>{label}</label>
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <button
          style={{ width: "32px", height: "32px", border: "1px solid #E8E0D8", borderRadius: "6px", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", background: "#FFFCF8", color: "#2C2420", fontSize: "16px" }}
          onClick={() => onChange(Math.max(min, value - step))}
        >−</button>
        <span style={{ minWidth: "60px", textAlign: "center", fontSize: "15px", fontWeight: 500 }}>{value.toLocaleString()}</span>
        <button
          style={{ width: "32px", height: "32px", border: "1px solid #E8E0D8", borderRadius: "6px", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", background: "#FFFCF8", color: "#2C2420", fontSize: "16px" }}
          onClick={() => onChange(Math.min(max, value + step))}
        >+</button>
      </div>
    </div>
  );
}
