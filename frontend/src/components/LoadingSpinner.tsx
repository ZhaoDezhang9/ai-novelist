import { colors } from "../styles";

interface LoadingSpinnerProps {
  size?: number;
  color?: string;
}

export default function LoadingSpinner({ size = 16, color = colors.primary }: LoadingSpinnerProps) {
  return (
    <>
      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
      <span style={{
        animation: "spin 1s linear infinite",
        fontSize: `${size}px`,
        color,
        display: "inline-block",
      }}>
        &#9696;
      </span>
    </>
  );
}
