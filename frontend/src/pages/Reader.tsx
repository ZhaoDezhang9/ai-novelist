import { useState } from "react";
import { colors, btn, shadows, radius, fonts } from "../styles";

type Tab = "reading" | "quality" | "emotion" | "characters" | "outline";

interface Chapter {
  number: number;
  title: string;
  wordCount: number;
  status: "done" | "writing" | "pending";
}

interface QualityCheck {
  name: string;
  passed: boolean;
  score: number;
  issues?: number;
}

interface Character {
  name: string;
  role: string;
  traits: string;
  arc: string;
  mentions: number;
}

const mockChapters: Chapter[] = [
  { number: 1, title: "灵气初觉", wordCount: 3218, status: "done" },
  { number: 2, title: "宗门大选", wordCount: 0, status: "writing" },
  { number: 3, title: "拜入山门", wordCount: 0, status: "pending" },
  { number: 4, title: "初入修行", wordCount: 0, status: "pending" },
  { number: 5, title: "灵根觉醒", wordCount: 0, status: "pending" },
];

const mockChapterContent = "青云城外三十里，有一座不起眼的小山丘。\n\n山丘上长满了枯黄的野草，在秋风中轻轻摇曳。夕阳的余晖洒落在山丘上，将那些野草染成了一片金黄。\n\n一个十五六岁的少年正坐在山丘顶上，望着远方的青云城发呆。他叫林远，是城中一个普通铁匠的儿子。\n\n\"远儿，该回家了。\"山脚下传来父亲的呼唤。\n\n林远站起身，拍了拍衣袍上的尘土，转身向山下走去。\n\n三日后，青云城贴出了告示：青云宗将于下月招收新弟子。\n\n林远攥着那张告示，心中激动难平。";

const mockQualityChecks: QualityCheck[] = [
  { name: "语言流畅", passed: true, score: 0.92 },
  { name: "情节合理", passed: true, score: 0.85 },
  { name: "人物一致", passed: true, score: 0.88 },
  { name: "伏笔埋设", passed: false, score: 0.62, issues: 2 },
  { name: "情绪节奏", passed: true, score: 0.78 },
  { name: "世界观融合", passed: true, score: 0.81 },
];

const mockCharacters: Character[] = [
{ name: "林远", role: "主角", traits: "坚韧、好奇心强、重情义", arc: "从凡人少年成长为一代宗师", mentions: 156 },
  { name: "林父", role: "配角", traits: "慈爱、朴实、手艺精湛", arc: "默默支持儿子追求仙道", mentions: 23 },
  { name: "青云宗长老", role: "导师", traits: "威严、深不可测、爱才", arc: "发现林远的特殊体质", mentions: 5 },
];

const mockOutline = [
  { chapter: 1, title: "灵气初觉", goal: "主角出场，建立平凡生活", emotionalBeat: "平静中带期待", act: "第一幕" },
  { chapter: 2, title: "宗门大选", goal: "展示主角的特殊天赋", emotionalBeat: "紧张、激动", act: "第一幕" },
  { chapter: 3, title: "拜入山门", goal: "主角正式踏入修行世界", emotionalBeat: "新奇、忐忑", act: "第二幕" },
  { chapter: 4, title: "初入修行", goal: "建立修行体系认知", emotionalBeat: "困惑中成长", act: "第二幕" },
  { chapter: 5, title: "灵根觉醒", goal: "主角发现隐藏天赋", emotionalBeat: "惊喜、震撼", act: "第二幕" },
];

const emotionPath = "M0,80 C50,70 100,60 150,50 C200,40 250,30 300,45 C350,60 400,75 450,60 C500,45 550,35 600,40 L600,100 L0,100 Z";

const s: Record<string, React.CSSProperties> = {
  readerLayout: { display: "grid", gridTemplateColumns: "260px 1fr", gap: 0, minHeight: "calc(100vh - 80px)" },
  chapterSidebar: { borderRight: `1px solid ${colors.border}`, padding: "24px 0", background: colors.surface, borderRadius: "10px 0 0 10px", overflowY: "auto" as const, maxHeight: "calc(100vh - 80px)", position: "sticky" as const, top: "40px" },
  chapterSidebarTitle: { fontFamily: fonts.display, fontSize: "15px", fontWeight: 600, padding: "0 20px 16px", borderBottom: `1px solid ${colors.borderLight}`, marginBottom: "8px", color: colors.fg },
  chapterList: { display: "flex", flexDirection: "column" as const },
  chapterItem: { display: "flex", alignItems: "center", gap: "10px", padding: "10px 20px", fontSize: "13px", cursor: "pointer", background: "none", border: "none", textAlign: "left" as const, width: "100%", transition: "all 0.15s", borderLeft: "3px solid transparent" },
  chapterItemActive: { background: colors.accentBg, borderLeftColor: colors.accent, color: colors.accent, fontWeight: 500 },
  chapterNum: { fontFamily: fonts.mono, fontSize: "11px", color: colors.muted, minWidth: "24px" },
  chapterTitle: { flex: 1 },
  chapterStatus: { width: "6px", height: "6px", borderRadius: "50%", marginLeft: "auto", flexShrink: 0 },
  chapterStatusDone: { background: colors.success },
  chapterStatusWriting: { background: colors.warning, animation: "pulse 1.5s infinite" },
  chapterStatusPending: { background: colors.border },
  readerMain: { minWidth: 0 },
  readerTabs: { display: "flex", gap: 0, borderBottom: `1px solid ${colors.border}`, padding: "0 24px", background: colors.surface, borderRadius: "0 10px 0 0" },
  readerTab: { padding: "14px 18px", fontSize: "13px", fontWeight: 500, color: colors.muted, borderBottom: "2px solid transparent", background: "none", border: "none", cursor: "pointer", transition: "all 0.15s" },
  readerTabActive: { color: colors.accent, borderBottomColor: colors.accent },
  readerPanel: { background: colors.bg },
  readingArea: { maxWidth: "680px", margin: "0 auto", padding: "40px 32px 60px", fontSize: "17px", lineHeight: 2, color: colors.fg },
  chapterHeader: { textAlign: "center" as const, marginBottom: "40px", paddingBottom: "24px", borderBottom: `1px solid ${colors.borderLight}` },
  chapterHeaderH2: { fontFamily: fonts.display, fontSize: "24px", fontWeight: 700, marginBottom: "8px", color: colors.fg },
  chapterMeta: { fontSize: "13px", color: colors.muted },
  readingText: { textAlign: "justify" as const },
  typewriterContainer: { position: "fixed", bottom: "32px", right: "32px", zIndex: 100 },
  typewriterBtn: { padding: "10px 20px", fontSize: "14px", boxShadow: shadows.hover },
  typewriterIcon: { marginRight: "8px" },
  typewriterSpinner: { marginRight: "8px", display: "inline-block", animation: "spin 1s linear infinite" },
  vizPanel: { padding: "24px 32px", minHeight: "calc(100vh - 140px)" },
  qualityGrid: { display: "grid", gridTemplateColumns: "280px 1fr", gap: "32px", maxWidth: "900px", margin: "0 auto" },
  radarContainer: { display: "flex", alignItems: "center", justifyContent: "center" },
  chartPlaceholder: { width: "100%", aspectRatio: "1", display: "flex", flexDirection: "column" as const, alignItems: "center", justifyContent: "center", background: colors.surface, borderRadius: radius.md, border: `1px solid ${colors.border}` },
  radarSvg: { width: "100%", height: "100%" },
  qualityDetails: { display: "flex", flexDirection: "column" as const, gap: "16px" },
  qualityTitle: { fontFamily: fonts.display, fontSize: "16px", fontWeight: 600, color: colors.fg, marginBottom: "8px" },
  qualityItem: { padding: "12px 16px", background: colors.surface, borderRadius: radius.sm, border: `1px solid ${colors.border}` },
  qualityItemHeader: { display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" },
  qualityStatus: { fontWeight: 700, fontSize: "14px" },
  qualityName: { flex: 1, fontSize: "13px", color: colors.fg },
  qualityScore: { fontSize: "13px", fontWeight: 600, color: colors.muted },
  qualityBar: { height: "4px", background: colors.borderLight, borderRadius: "2px", overflow: "hidden" },
  qualityBarFill: { height: "100%", borderRadius: "2px", transition: "width 0.3s" },
  qualityIssues: { fontSize: "11px", color: colors.warning, marginTop: "6px" },
  emotionContainer: { maxWidth: "900px", margin: "0 auto" },
  emotionHeader: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" },
  emotionTitle: { fontFamily: fonts.display, fontSize: "16px", fontWeight: 600, color: colors.fg },
  emotionLegend: { display: "flex", gap: "16px" },
  emotionLegendItem: { display: "flex", alignItems: "center", gap: "6px", fontSize: "12px", color: colors.muted },
  emotionLegendDot: { width: "8px", height: "8px", borderRadius: "50%" },
  emotionSvg: { width: "100%", height: "120px", background: colors.surface, borderRadius: radius.md, border: `1px solid ${colors.border}`, padding: "16px" },
  emotionNotes: { display: "flex", gap: "16px", marginTop: "24px", flexWrap: "wrap" as const },
  emotionNote: { display: "flex", alignItems: "center", gap: "8px", padding: "10px 14px", background: colors.surface, borderRadius: radius.sm, border: `1px solid ${colors.border}`, fontSize: "13px", color: colors.fgSecondary },
  emotionNoteIcon: { fontSize: "14px" },
  charactersGrid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "32px", maxWidth: "1000px", margin: "0 auto" },
  graphSvg: { width: "100%", height: "auto" },
  graphPlaceholderText: { fontSize: "12px", color: colors.muted, marginTop: "8px", textAlign: "center" as const },
  characterCards: { display: "flex", flexDirection: "column" as const, gap: "16px" },
  characterCardsTitle: { fontFamily: fonts.display, fontSize: "16px", fontWeight: 600, color: colors.fg, marginBottom: "8px" },
  characterCard: { padding: "16px", background: colors.surface, borderRadius: radius.md, border: `1px solid ${colors.border}` },
  characterCardHeader: { display: "flex", alignItems: "center", gap: "10px", marginBottom: "10px" },
  characterName: { fontSize: "15px", fontWeight: 600, color: colors.fg },
  characterRole: { padding: "2px 8px", fontSize: "11px", borderRadius: radius.sm, fontWeight: 500 },
  characterTraits: { fontSize: "13px", color: colors.fgSecondary, marginBottom: "8px" },
  characterArc: { fontSize: "12px", color: colors.muted, marginBottom: "6px" },
  characterArcLabel: { color: colors.fgSecondary },
  characterMentions: { fontSize: "11px", color: colors.muted },
  outlineContainer: { maxWidth: "700px", margin: "0 auto" },
  outlineTitle: { fontFamily: fonts.display, fontSize: "16px", fontWeight: 600, color: colors.fg, marginBottom: "24px", textAlign: "center" as const },
  outlineAct: { marginBottom: "32px" },
  outlineActTitle: { fontSize: "14px", fontWeight: 600, color: colors.accent, marginBottom: "16px", paddingBottom: "8px", borderBottom: `1px solid ${colors.borderLight}` },
  outlineChapter: { padding: "14px 16px", background: colors.surface, borderRadius: radius.sm, border: `1px solid ${colors.border}`, marginBottom: "12px" },
  outlineChapterTitle: { fontSize: "14px", fontWeight: 600, color: colors.fg, marginBottom: "6px" },
  outlineChapterGoal: { fontSize: "13px", color: colors.fgSecondary, marginBottom: "4px" },
  outlineChapterBeat: { fontSize: "12px", color: colors.muted },
};
export default function Reader() {
  const [activeTab, setActiveTab] = useState<Tab>("reading");
  const [selectedChapter, setSelectedChapter] = useState(1);
  const [typewriterActive, setTypewriterActive] = useState(false);

  const tabLabels: Record<Tab, string> = {
    reading: "阅读",
    quality: "质量检测",
    emotion: "情绪曲线",
    characters: "角色图谱",
    outline: "大纲",
  };

  const handleTypewriter = () => {
    setTypewriterActive(true);
    setTimeout(() => setTypewriterActive(false), 3000);
  };

  return (
    <div style={s.readerLayout}>
      <style>{"@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } } @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }"}</style>

      <aside style={s.chapterSidebar}>
        <div style={s.chapterSidebarTitle}>章节目录</div>
        <div style={s.chapterList}>
          {mockChapters.map((ch) => (
            <button
              key={ch.number}
              onClick={() => setSelectedChapter(ch.number)}
              style={{
                ...s.chapterItem,
                ...(selectedChapter === ch.number ? s.chapterItemActive : {}),
              }}
            >
              <span style={s.chapterNum}>{String(ch.number).padStart(2, "0")}</span>
              <span style={s.chapterTitle}>{ch.title}</span>
              <span style={{
                ...s.chapterStatus,
                ...(ch.status === "done" ? s.chapterStatusDone : {}),
                ...(ch.status === "writing" ? s.chapterStatusWriting : {}),
                ...(ch.status === "pending" ? s.chapterStatusPending : {}),
              }} />
            </button>
          ))}
        </div>
      </aside>

      <main style={s.readerMain}>
        <div style={s.readerTabs}>
          {(Object.keys(tabLabels) as Tab[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                ...s.readerTab,
                ...(activeTab === tab ? s.readerTabActive : {}),
              }}
            >
              {tabLabels[tab]}
            </button>
          ))}
        </div>

        {activeTab === "reading" && (
          <div style={s.readerPanel}>
            <div style={s.readingArea}>
              <div style={s.chapterHeader}>
                <h2 style={s.chapterHeaderH2}>
                  第{selectedChapter}章 · {mockChapters.find(c => c.number === selectedChapter)?.title}
                </h2>
                <div style={s.chapterMeta}>3,218 字 · 已通过 6 项质量检测</div>
              </div>
              <div style={s.readingText}>
                {mockChapterContent.split("\n\n").map((para, i) => (
                  <p key={i} style={{ marginBottom: "1.8em", textIndent: "2em" }}>{para}</p>
                ))}
              </div>
            </div>
            <div style={s.typewriterContainer}>
              <button
                onClick={handleTypewriter}
                disabled={typewriterActive}
                style={{
                  ...btn.primary,
                  ...s.typewriterBtn,
                  opacity: typewriterActive ? 0.7 : 1,
                }}
              >
{typewriterActive ? (
                  <>
                    <span style={s.typewriterSpinner}>⟳</span>
                    续写中...
                  </>
                ) : (
                  <>
                    <span style={s.typewriterIcon}>✎</span>
                    续写下一章
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {activeTab === "quality" && (
          <div style={s.readerPanel}>
            <div style={s.vizPanel}>
              <div style={s.qualityGrid}>
                <div style={s.radarContainer}>
                  <div style={s.chartPlaceholder}>
                    <svg viewBox="0 0 200 200" style={s.radarSvg}>
                      <circle cx="100" cy="100" r="80" fill="none" stroke={colors.border} strokeWidth="1" />
                      <circle cx="100" cy="100" r="60" fill="none" stroke={colors.border} strokeWidth="1" />
                      <circle cx="100" cy="100" r="40" fill="none" stroke={colors.border} strokeWidth="1" />
                      <circle cx="100" cy="100" r="20" fill="none" stroke={colors.border} strokeWidth="1" />
                      {[0, 60, 120, 180, 240, 300].map((angle) => (
                        <line
                          key={angle}
                          x1="100" y1="100"
                          x2={100 + 80 * Math.cos((angle * Math.PI) / 180)}
                          y2={100 + 80 * Math.sin((angle * Math.PI) / 180)}
                          stroke={colors.border} strokeWidth="1"
                        />
                      ))}
                      <polygon
                        points={mockQualityChecks.map((q, i) => {
                          const angle = (i * 60 - 90) * (Math.PI / 180);
                          const r = q.score * 80;
                          return `${100 + r * Math.cos(angle)},${100 + r * Math.sin(angle)}`;
                        }).join(" ")}
                        fill={colors.accent} fillOpacity="0.3"
                        stroke={colors.accent} strokeWidth="2"
                      />
                      {mockQualityChecks.map((q, i) => {
                        const angle = (i * 60 - 90) * (Math.PI / 180);
                        const x = 100 + 95 * Math.cos(angle);
                        const y = 100 + 95 * Math.sin(angle);
                        return (
                          <text key={i} x={x} y={y} textAnchor="middle" dominantBaseline="middle" fontSize="10" fill={colors.fgSecondary}>
                            {q.name}
                          </text>
                        );
                      })}
                    </svg>
                  </div>
                </div>
                <div style={s.qualityDetails}>
                  <h3 style={s.qualityTitle}>质量检测详情</h3>
                  {mockQualityChecks.map((check, i) => (
                    <div key={i} style={s.qualityItem}>
                      <div style={s.qualityItemHeader}>
                        <span style={{ ...s.qualityStatus, color: check.passed ? colors.success : colors.danger }}>
                          {check.passed ? "✓" : "✗"}
                        </span>
                        <span style={s.qualityName}>{check.name}</span>
                        <span style={s.qualityScore}>{(check.score * 100).toFixed(0)}%</span>
                      </div>
                      <div style={s.qualityBar}>
                        <div style={{ ...s.qualityBarFill, width: `${check.score * 100}%`, background: check.passed ? colors.success : colors.danger }} />
                      </div>
                      {check.issues && <div style={s.qualityIssues}>发现 {check.issues} 个问题待优化</div>}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "emotion" && (
          <div style={s.readerPanel}>
            <div style={s.vizPanel}>
              <div style={s.emotionContainer}>
                <div style={s.emotionHeader}>
                  <h3 style={s.emotionTitle}>情绪曲线</h3>
                  <div style={s.emotionLegend}>
                    <span style={s.emotionLegendItem}>
                      <span style={{ ...s.emotionLegendDot, background: colors.accent }} />
                      本章情绪
                    </span>
                  </div>
                </div>
                <svg viewBox="0 0 900 120" style={s.emotionSvg}>
                  <line x1="0" y1="20" x2="900" y2="20" stroke={colors.border} strokeWidth="1" strokeDasharray="4" />
                  <line x1="0" y1="50" x2="900" y2="50" stroke={colors.border} strokeWidth="1" strokeDasharray="4" />
                  <line x1="0" y1="80" x2="900" y2="80" stroke={colors.border} strokeWidth="1" strokeDasharray="4" />
                  <path d={emotionPath} fill={colors.accent} fillOpacity="0.2" stroke={colors.accent} strokeWidth="2" />
                  <text x="10" y="15" fontSize="9" fill={colors.muted}>高</text>
                  <text x="10" y="50" fontSize="9" fill={colors.muted}>中</text>
                  <text x="10" y="85" fontSize="9" fill={colors.muted}>低</text>
                  {[1, 2, 3, 4, 5].map((ch, i) => (
                    <g key={ch}>
                      <line x1={(i + 1) * 150} y1="100" x2={(i + 1) * 150} y2="105" stroke={colors.border} strokeWidth="1" />
                      <text x={(i + 1) * 150} y="115" textAnchor="middle" fontSize="9" fill={colors.muted}>{ch}</text>
                    </g>
                  ))}
                </svg>
                <div style={s.emotionNotes}>
                  <div style={s.emotionNote}>
                    <span style={s.emotionNoteIcon}>📍</span>
                    开篇平静，为后续转折铺垫
                  </div>
                  <div style={s.emotionNote}>
                    <span style={s.emotionNoteIcon}>📍</span>
                    中段期待感逐渐攀升
                  </div>
                  <div style={s.emotionNote}>
                    <span style={s.emotionNoteIcon}>📍</span>
                    结尾悬念留白，情绪回落
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "characters" && (
          <div style={s.readerPanel}>
            <div style={s.vizPanel}>
              <div style={s.charactersGrid}>
                <div style={s.radarContainer}>
                  <div style={s.chartPlaceholder}>
                    <svg viewBox="0 0 400 300" style={s.graphSvg}>
                      <line x1="80" y1="80" x2="200" y2="150" stroke={colors.border} strokeWidth="2" />
                      <line x1="320" y1="100" x2="200" y2="150" stroke={colors.border} strokeWidth="2" />
                      <line x1="200" y1="150" x2="200" y2="240" stroke={colors.border} strokeWidth="2" />
                      <circle cx="80" cy="80" r="30" fill={colors.accentBg} stroke={colors.accent} strokeWidth="2" />
                      <text x="80" y="85" textAnchor="middle" fontSize="12" fill={colors.fg}>林远</text>
                      <circle cx="320" cy="100" r="25" fill={colors.surface} stroke={colors.border} strokeWidth="2" />
                      <text x="320" y="105" textAnchor="middle" fontSize="11" fill={colors.fgSecondary}>林父</text>
                      <circle cx="200" cy="150" r="35" fill={colors.primaryMuted} stroke={colors.primary} strokeWidth="2" />
                      <text x="200" y="155" textAnchor="middle" fontSize="12" fill={colors.primary}>青云宗</text>
                      <circle cx="200" cy="240" r="25" fill={colors.surface} stroke={colors.border} strokeWidth="2" />
                      <text x="200" y="245" textAnchor="middle" fontSize="11" fill={colors.fgSecondary}>长老</text>
                    </svg>
                    <div style={s.graphPlaceholderText}>角色关系图</div>
                  </div>
                </div>
                <div style={s.characterCards}>
                  <h3 style={s.characterCardsTitle}>角色信息</h3>
                  {mockCharacters.map((char, i) => (
                    <div key={i} style={s.characterCard}>
                      <div style={s.characterCardHeader}>
                        <span style={s.characterName}>{char.name}</span>
                        <span style={{
                          ...s.characterRole,
                          background: char.role === "主角" ? colors.accentBg : colors.surface,
                          color: char.role === "主角" ? colors.accent : colors.muted,
                        }}>
                          {char.role}
                        </span>
                      </div>
                      <div style={s.characterTraits}>{char.traits}</div>
                      <div style={s.characterArc}>
                        <span style={s.characterArcLabel}>成长弧线：</span>{char.arc}
                      </div>
                      <div style={s.characterMentions}>出场 {char.mentions} 次</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "outline" && (
          <div style={s.readerPanel}>
            <div style={s.vizPanel}>
              <div style={s.outlineContainer}>
                <h3 style={s.outlineTitle}>故事大纲</h3>
                {["第一幕", "第二幕"].map((act) => (
                  <div key={act} style={s.outlineAct}>
                    <div style={s.outlineActTitle}>{act}</div>
                    {mockOutline.filter(o => o.act === act).map((item) => (
                      <div key={item.chapter} style={s.outlineChapter}>
                        <div style={s.outlineChapterTitle}>
                          第{item.chapter}章 · {item.title}
                        </div>
                        <div style={s.outlineChapterGoal}>{item.goal}</div>
                        <div style={s.outlineChapterBeat}>情绪：{item.emotionalBeat}</div>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
