import React from "react";
import { colors, space, font } from "../styles";

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  ErrorBoundaryState
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  handleReload = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          minHeight: "100vh",
          padding: space[6],
          textAlign: "center",
          background: colors.bg,
          color: colors.text,
        }}>
          <div style={{ fontSize: "48px", marginBottom: space[4] }}>⚠️</div>
          <h2 style={{ ...font.xl, fontWeight: 700, marginBottom: space[3] }}>出错了</h2>
          <p style={{ ...font.md, color: colors.textMuted, marginBottom: space[6], maxWidth: "400px" }}>
            {this.state.error?.message || "页面加载失败，请尝试重新加载"}
          </p>
          <button
            onClick={this.handleReload}
            style={{
              padding: `${space[3]} ${space[6]}`,
              fontSize: "14px",
              fontWeight: 600,
              background: colors.primary,
              color: "#fff",
              border: "none",
              borderRadius: "8px",
              cursor: "pointer",
            }}
          >
            重新加载
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
