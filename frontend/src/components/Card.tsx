import React from "react";
import { card } from "../styles";

interface CardProps {
  children: React.ReactNode;
  onClick?: () => void;
  style?: React.CSSProperties;
  className?: string;
}

export default function Card({ children, onClick, style, className }: CardProps) {
  return (
    <div
      className={className}
      onClick={onClick}
      style={{
        ...card,
        cursor: onClick ? "pointer" : undefined,
        ...style,
      }}
    >
      {children}
    </div>
  );
}
