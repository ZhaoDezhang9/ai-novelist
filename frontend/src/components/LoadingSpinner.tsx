import { colors } from "../styles";

interface LoadingSpinnerProps {
  size?: number;
  color?: string;
}

const styleId = "loading-spinner-keyframes";
if (!document.getElementById(styleId)) {
  const style = document.createElement("style");
  style.id = styleId;
  style.textContent = "@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }";
  document.head.appendChild(style);
}

export default function LoadingSpinner({ size = 16, color = colors.primary }: LoadingSpinnerProps) {
  return (
    <span style={{
      animation: "spin 1s linear infinite",
      fontSize: `${size}px`,
      color,
      display: "inline-block",
    }}>
      &#9696;
    </span>
  );
}
