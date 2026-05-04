import { colors, space } from "../styles";

interface Tab {
  id: string;
  label: string;
}

interface TabPanelProps {
  tabs: Tab[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
}

export default function TabPanel({ tabs, activeTab, onTabChange }: TabPanelProps) {
  return (
    <div style={{
      display: "flex",
      gap: "4px",
      marginBottom: space[5],
      borderBottom: `1px solid ${colors.border}`,
    }}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          style={{
            padding: `${space[2]} ${space[4]}`,
            fontSize: "13px",
            background: "none",
            border: "none",
            cursor: "pointer",
            color: activeTab === tab.id ? colors.primary : colors.textMuted,
            borderBottom: activeTab === tab.id ? `2px solid ${colors.primary}` : "2px solid transparent",
            fontWeight: activeTab === tab.id ? 600 : 400,
          }}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
