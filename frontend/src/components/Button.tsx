import React from "react";
import { btn as btnStyles } from "../styles";

type ButtonVariant = "primary" | "secondary" | "danger" | "ghost" | "warning";

interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: ButtonVariant;
  disabled?: boolean;
  style?: React.CSSProperties;
  type?: "button" | "submit";
  title?: string;
}

const variantMap: Record<ButtonVariant, React.CSSProperties> = {
  primary: btnStyles.primary,
  secondary: btnStyles.ghost,
  danger: btnStyles.danger,
  ghost: btnStyles.ghost,
  warning: btnStyles.warning,
};

export default function Button({
  children,
  onClick,
  variant = "primary",
  disabled = false,
  style,
  type = "button",
  title,
}: ButtonProps) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      title={title}
      style={{
        ...variantMap[variant],
        opacity: disabled ? 0.6 : 1,
        cursor: disabled ? "not-allowed" : "pointer",
        ...style,
      }}
    >
      {children}
    </button>
  );
}
