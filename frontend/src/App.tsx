import React, { useState } from "react";
import { Routes, Route, Link, useLocation } from "react-router-dom";
import StoryList from "./pages/StoryList";
import StoryCreate from "./pages/StoryCreate";
import StoryDetail from "./pages/StoryDetail";
import Settings from "./pages/Settings";
import { GenerationProvider, useGeneration } from "./GenerationContext";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider, useTheme } from "./ThemeContext";
import { colors, layout, font, space, bp, scrollbar, shadows, radius, fonts } from "./styles";

const NAV_ITEMS = [
  { path: "/", label: "小说集" },
  { path: "/create", label: "创作" },
  { path: "/story/", label: "书房" },
  { path: "/settings", label: "设定" },
];

// SVG Icons for nav items
const NavIcons = {
  home: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>,
  create: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>,
  reader: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>,
  settings: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>,
};

const STATUS_LABELS: Record<string, string> = {
  generating: "生成中",
  checking: "质检中",
  rewriting: "改写中",
  saving: "保存中",
};

function GlobalProgressBar() {
  const { activeGenerations, hasAnyActive } = useGeneration();
  if (!hasAnyActive) return null;

  const active = Array.from(activeGenerations.values()).find(
    (g) => g.status !== "idle" && g.status !== "complete"
  );
  if (!active) return null;

  return (
    <div style={{
      padding: `${space[2]} ${space[3]}`,
      background: colors.primaryMuted,
      borderRadius: "6px",
      marginBottom: space[3],
      border: `1px solid ${colors.primaryBorder}`,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: space[2], marginBottom: space[1] }}>
        <span style={{ animation: "spin 1s linear infinite", fontSize: "12px", color: colors.primary }}>&#9696;</span>
        <span style={{ ...font.xs, fontWeight: 600, color: colors.primary }}>
          {STATUS_LABELS[active.status] || active.status} · 第{active.chapterNumber}章
        </span>
      </div>
      {active.tokensReceived > 0 && (
        <div style={{ ...font.xs, color: colors.textDim }}>
          {active.tokensReceived} tokens
        </div>
      )}
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <GenerationProvider>
          <AppInner />
        </GenerationProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

function AppInner() {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: colors.bg, color: colors.fg, ...scrollbar }}>
      {/* Mobile Header */}
      <header className="mobile-header" style={{
        display: "none",
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        height: "56px",
        background: colors.surface,
        borderBottom: `1px solid ${colors.border}`,
        alignItems: "center",
        padding: `0 ${space[4]}`,
        gap: space[3],
        zIndex: 90,
      }}>
        <button
          onClick={() => setSidebarOpen(true)}
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            width: "36px",
            height: "36px",
            border: "none",
            background: "transparent",
            cursor: "pointer",
            color: colors.fg,
            borderRadius: radius.sm,
          }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/>
          </svg>
        </button>
        <span style={{ ...font.md, fontWeight: 700, fontFamily: fonts.display, color: colors.fg }}>
          AI <span style={{ color: colors.accent }}>小说家</span>
        </span>
      </header>

      {/* Sidebar Overlay */}
      <div
        className="sidebar-overlay"
        onClick={() => setSidebarOpen(false)}
        style={{
          display: sidebarOpen ? "block" : "none",
          position: "fixed",
          inset: 0,
          background: "rgba(0,0,0,0.4)",
          zIndex: 150,
        }}
      />

      {/* Sidebar */}
      <aside style={{
        width: "220px",
        flexShrink: 0,
        background: colors.surface,
        borderRight: `1px solid ${colors.border}`,
        display: "flex",
        flexDirection: "column",
        padding: "28px 0 20px",
        position: "fixed",
        top: 0,
        left: 0,
        bottom: 0,
        zIndex: 100,
        transform: sidebarOpen ? "translateX(0)" : undefined,
      }}>
        {/* Brand */}
        <div style={{
          fontFamily: fonts.display,
          fontSize: "20px",
          fontWeight: 700,
          padding: `0 24px 24px`,
          color: colors.fg,
          letterSpacing: ".02em",
        }}>
          AI <span style={{ color: colors.accent }}>小说家</span>
        </div>

        {/* Global progress */}
        <div style={{ padding: `${space[3]} ${space[3]} 0` }}>
          <GlobalProgressBar />
        </div>

        {/* Nav */}
        <nav style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          gap: "2px",
          padding: "0 10px",
        }}>
          {NAV_ITEMS.map((item, index) => {
            const isActive = item.path === "/"
              ? location.pathname === "/"
              : location.pathname.startsWith(item.path);
            const iconKeys = ["home", "create", "reader", "settings"] as const;
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setSidebarOpen(false)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "10px",
                  padding: "10px 14px",
                  borderRadius: "6px",
                  fontSize: "14px",
                  color: isActive ? colors.accent : colors.fgSecondary,
                  background: isActive ? colors.accentBg : "transparent",
                  fontWeight: isActive ? 500 : 400,
                  textDecoration: "none",
                  transition: "all 0.15s",
                }}
              >
                <span style={{ color: isActive ? colors.accent : colors.fgSecondary }}>{NavIcons[iconKeys[index]]}</span>
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Footer - Theme Toggle */}
        <div style={{
          padding: `0 10px`,
        }}>
          <button
            onClick={toggleTheme}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              width: "100%",
              padding: "10px 14px",
              borderRadius: "6px",
              fontSize: "14px",
              color: colors.fgSecondary,
              background: "transparent",
              border: "none",
              cursor: "pointer",
              transition: "all 0.15s",
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              {theme === "dark" ? (
                <>
                  <circle cx="12" cy="12" r="5"/>
                  <line x1="12" y1="1" x2="12" y2="3"/>
                  <line x1="12" y1="21" x2="12" y2="23"/>
                  <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                  <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                  <line x1="1" y1="12" x2="3" y2="12"/>
                  <line x1="21" y1="12" x2="23" y2="12"/>
                  <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                  <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
                </>
              ) : (
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
              )}
            </svg>
            {theme === "dark" ? "浅色模式" : "深色模式"}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main style={{
        ...layout.main,
        overflow: "auto",
        height: "100vh",
        paddingTop: "56px",
      }}>
        <div style={layout.page}>
          <Routes>
            <Route path="/" element={<StoryList />} />
            <Route path="/create" element={<StoryCreate />} />
            <Route path="/story/:id" element={<StoryDetail />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </div>
      </main>

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        ${bp.md} {
          .mobile-header { display: flex !important; }
          .sidebar-overlay { display: none !important; }
        }
        [data-theme="dark"] {
          --bg: #1A1714;
          --bg-warm: #201D19;
          --surface: #262220;
          --surface-raised: #2E2A27;
          --fg: #E8E0D8;
          --fg-secondary: #C4B8AC;
          --muted: #8C7E72;
          --border: #3A3430;
          --accent: #D4795E;
          --accent-hover: #E08A6F;
          --accent-bg: oklch(28% 0.04 45);
          --primary: #8CB67A;
          --primary-hover: #9DC68C;
          --success: #8CB67A;
          --warning: #D4A84A;
          --danger: #D46A5A;
          --info: #7AA0B0;
        }
      `}</style>
    </div>
  );
}
