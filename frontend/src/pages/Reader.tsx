import { useState, useEffect, useCallback, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { api, type ChapterInfo, type ChapterDetail, type StoryDetail } from "../services/api";
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from "recharts";
import { colors, fonts, radius, space, shadows } from "../styles";

const LS_PROGRESS_KEY = "reader-progress";

function loadProgress(storyId: string): { chapterNumber: number; scrollPct: number } | null {
  try {
    const raw = localStorage.getItem(`${LS_PROGRESS_KEY}-${storyId}`);
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

function saveProgress(storyId: string, chapterNumber: number, scrollPct: number) {
  localStorage.setItem(`${LS_PROGRESS_KEY}-${storyId}`, JSON.stringify({ chapterNumber, scrollPct }));
}

const tabDefs = [
  { id: "reading", label: "阅读" },
  { id: "quality", label: "质量检测" },
  { id: "emotion", label: "情绪曲线" },
  { id: "characters", label: "角色图谱" },
  { id: "outline", label: "大纲" },
] as const;
type Tab = typeof tabDefs[number]["id"];

export default function Reader() {
  const { id } = useParams<{ id: string }>();
  const [story, setStory] = useState<StoryDetail | null>(null);
  const [chapters, setChapters] = useState<ChapterInfo[]>([]);
  const [selectedChapter, setSelectedChapter] = useState<ChapterDetail | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("reading");
  const [loading, setLoading] = useState(true);
  const [chapterLoading, setChapterLoading] = useState(false);
  const [error, setError] = useState("");
  const [allContent, setAllContent] = useState<Map<number, string>>(new Map());
  const contentRef = useRef<HTMLDivElement>(null);

  // Load story + chapter list
  useEffect(() => {
    if (!id) return;
    setLoading(true);
    Promise.all([api.getStory(id), api.listChapters(id)])
      .then(([s, c]) => { setStory(s); setChapters(c); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  // Restore reading progress
  useEffect(() => {
    if (!id || chapters.length === 0) return;
    const progress = loadProgress(id);
    if (progress) {
      loadChapter(progress.chapterNumber);
    }
  }, [id, chapters]);

  // Scroll position persistence
  useEffect(() => {
    if (!id || !selectedChapter) return;
    const el = contentRef.current;
    if (!el) return;
    const onScroll = () => {
      const pct = el.scrollTop / (el.scrollHeight - el.clientHeight);
      saveProgress(id, selectedChapter.chapter_number, pct);
    };
    el.addEventListener("scroll", onScroll, { passive: true });
    return () => el.removeEventListener("scroll", onScroll);
  }, [id, selectedChapter]);

  const loadChapter = useCallback(async (num: number) => {
    if (!id) return;
    setChapterLoading(true);
    try {
      const ch = await api.getChapter(id, num);
      setSelectedChapter(ch);
      setAllContent((prev) => { const n = new Map(prev); n.set(num, ch.content); return n; });
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载章节失败");
    } finally {
      setChapterLoading(false);
    }
  }, [id]);

  if (loading) return <div style={style.centered}>加载中...</div>;
  if (error && !story) return <div style={{ ...style.centered, color: colors.danger }}>{error}</div>;
  if (!story) return <div style={style.centered}>故事不存在</div>;

  const doneChapters = chapters.filter((c) => c.status === "accepted" || c.status === "published").length;

  return (
    <div style={style.layout}>
      <aside style={style.sidebar}>
        <div style={style.sidebarHeader}>
          <Link to={`/story/${id}`} style={style.backLink}>&larr; 返回详情</Link>
          <div style={style.sidebarTitle}>章节目录</div>
          <div style={style.chapterCount}>{chapters.length} 章</div>
        </div>
        <div style={style.chapterList}>
          {chapters.map((ch) => (
            <button
              key={ch.chapter_number}
              onClick={() => loadChapter(ch.chapter_number)}
              style={{
                ...style.chapterItem,
                ...(selectedChapter?.chapter_number === ch.chapter_number ? style.chapterItemActive : {}),
              }}
            >
              <span style={style.chapterNum}>{String(ch.chapter_number).padStart(2, "0")}</span>
              <span style={style.chapterTitle}>{ch.title}</span>
              <span style={{
                ...style.chapterDot,
                background: ch.status === "published" || ch.status === "accepted" ? colors.success
                  : ch.status === "draft" ? colors.warning : colors.border,
              }} />
            </button>
          ))}
        </div>
      </aside>

      <main style={style.main}>
        <div style={style.tabs}>
          {tabDefs.map((tab) => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)}
              style={{ ...style.tab, ...(activeTab === tab.id ? style.tabActive : {}) }}>
              {tab.label}
            </button>
          ))}
        </div>

        {activeTab === "reading" && (
          <div style={style.readingPanel}>
            {chapterLoading ? (
              <div style={style.centered}>加载中...</div>
            ) : selectedChapter ? (
              <div ref={contentRef} style={style.readingArea}>
                <div style={style.chapterHeader}>
                  <h2 style={style.chapterH2}>第{selectedChapter.chapter_number}章 · {selectedChapter.title}</h2>
                  <div style={style.chapterMeta}>
                    {selectedChapter.content.replace(/\s/g, "").length} 字
                    {selectedChapter.rewrites_count > 0 && ` · 已改写${selectedChapter.rewrites_count}次`}
                  </div>
                </div>
                <div style={style.readingText}>
                  {selectedChapter.content.split("\n\n").map((para, i) => (
                    <p key={i} style={{ marginBottom: "1.8em", textIndent: "2em" }}>{para}</p>
                  ))}
                </div>
              </div>
            ) : (
              <div style={style.centered}>选择左侧章节开始阅读</div>
            )}
          </div>
        )}

        {activeTab === "quality" && selectedChapter && (
          <div style={style.vizPanel}>
            <div style={style.vizGrid}>
              <div style={style.chartWrap}>
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={(selectedChapter.check_results || []).map((cr) => ({
                    name: cr.layer,
                    score: cr.scores ? Object.values(cr.scores).reduce((a, b) => a + b, 0) / Object.values(cr.scores).length : (cr.passed ? 0.9 : 0.5),
                  }))}>
                    <PolarGrid stroke={colors.border} />
                    <PolarAngleAxis dataKey="name" tick={{ fontSize: 11, fill: colors.fgSecondary }} />
                    <PolarRadiusAxis domain={[0, 1]} tick={false} axisLine={false} />
                    <Radar dataKey="score" stroke={colors.accent} fill={colors.accent} fillOpacity={0.3} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
              <div style={style.qualityList}>
                <h3 style={style.vizTitle}>质量检测详情</h3>
                {(selectedChapter.check_results || []).map((cr, i) => (
                  <div key={i} style={style.qualityItem}>
                    <div style={style.qualityHeader}>
                      <span style={{ color: cr.passed ? colors.success : colors.danger, fontWeight: 700, fontSize: 14 }}>
                        {cr.passed ? "\u2713" : "\u2717"}
                      </span>
                      <span style={{ flex: 1, fontSize: 13, color: colors.fg }}>{cr.layer}</span>
                      <span style={{ fontSize: 13, fontWeight: 600, color: colors.muted }}>
                        {cr.scores ? Math.round(Object.values(cr.scores).reduce((a,b)=>a+b,0)/Object.values(cr.scores).length*100) : (cr.passed ? 90 : 50)}%
                      </span>
                    </div>
                    <div style={{ height: 4, background: colors.borderLight, borderRadius: 2, overflow: "hidden" }}>
                      <div style={{ height: "100%", width: `${(cr.scores ? Object.values(cr.scores).reduce((a,b)=>a+b,0)/Object.values(cr.scores).length : (cr.passed?0.9:0.5))*100}%`, background: cr.passed ? colors.success : colors.danger, borderRadius: 2 }} />
                    </div>
                    {cr.issues_count > 0 && <div style={{ fontSize: 11, color: colors.warning, marginTop: 6 }}>发现 {cr.issues_count} 个问题</div>}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === "emotion" && selectedChapter && (
          <div style={style.vizPanel}>
            <div style={style.vizTitle}>情绪曲线</div>
            {selectedChapter.emotion_curve?.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={selectedChapter.emotion_curve.map((p) => ({ pos: p.position_pct, tension: p.tension, relaxation: p.relaxation, sadness: p.sadness, pleasure: p.pleasure }))}>
                  <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
                  <XAxis dataKey="pos" tick={{ fontSize: 11, fill: colors.muted }} />
                  <YAxis domain={[0, 1]} tick={{ fontSize: 11, fill: colors.muted }} />
                  <Tooltip contentStyle={{ background: colors.surfaceRaised, border: `1px solid ${colors.border}`, borderRadius: 6, fontSize: 12, color: colors.fg }} />
                  <Area type="monotone" dataKey="tension" stroke={colors.danger} fill={colors.danger} fillOpacity={0.15} />
                  <Area type="monotone" dataKey="pleasure" stroke={colors.success} fill={colors.success} fillOpacity={0.15} />
                  <Area type="monotone" dataKey="sadness" stroke={colors.info} fill={colors.info} fillOpacity={0.15} />
                  <Area type="monotone" dataKey="relaxation" stroke={colors.accent} fill={colors.accent} fillOpacity={0.15} />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ color: colors.muted, textAlign: "center", padding: space[8] }}>暂无情绪曲线数据</div>
            )}
          </div>
        )}

        {activeTab === "characters" && story && (
          <div style={style.vizPanel}>
            <div style={style.charGrid}>
              <div style={style.chartWrap}>
                <CharacterGraph characters={story.characters || []} />
              </div>
              <div style={style.characterCards}>
                <h3 style={style.vizTitle}>角色信息</h3>
                {(story.characters || []).map((c, i) => (
                  <div key={i} style={style.charCard}>
                    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
                      <span style={{ fontSize: 15, fontWeight: 600, color: colors.fg }}>{c.name}</span>
                      <span style={{ padding: "2px 8px", fontSize: 11, borderRadius: radius.sm, fontWeight: 500, background: c.role === "主角" ? colors.accentBg : colors.bgWarm, color: c.role === "主角" ? colors.accent : colors.muted }}>
                        {c.role}
                      </span>
                    </div>
                    {c.traits && <div style={{ fontSize: 13, color: colors.fgSecondary, marginBottom: 8 }}>{c.traits}</div>}
                    {c.arc && <div style={{ fontSize: 12, color: colors.muted }}>成长弧线：{c.arc}</div>}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === "outline" && story && (
          <div style={style.vizPanel}>
            <h3 style={{ ...style.vizTitle, textAlign: "center" }}>故事大纲</h3>
            {groupByAct(story.outline || []).map(([act, nodes]) => (
              <div key={act} style={{ marginBottom: 32 }}>
                <div style={{ fontSize: 14, fontWeight: 600, color: colors.accent, marginBottom: 16, paddingBottom: 8, borderBottom: `1px solid ${colors.borderLight}` }}>{act}</div>
                {nodes.map((node) => {
                  const ch = chapters.find((c) => c.chapter_number === node.chapter);
                  const isDone = ch && (ch.status === "accepted" || ch.status === "published");
                  return (
                    <div key={node.chapter} style={{ padding: "14px 16px", background: colors.surface, borderRadius: radius.sm, border: `1px solid ${isDone ? colors.successBorder : colors.border}`, marginBottom: 12 }}>
                      <div style={{ fontSize: 14, fontWeight: 600, color: colors.fg, marginBottom: 6 }}>
                        第{node.chapter}章 · {node.title}
                        {isDone && <span style={{ marginLeft: 8, fontSize: 11, color: colors.success }}>&#10003;</span>}
                      </div>
                      <div style={{ fontSize: 13, color: colors.fgSecondary, marginBottom: 4 }}>{node.goal}</div>
                      <div style={{ fontSize: 12, color: colors.muted }}>情绪：{node.emotional_beat}</div>
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

function groupByAct(outline: any[]): [string, any[]][] {
  const map = new Map<string, any[]>();
  for (const node of outline) {
    const act = node.act || "未知";
    if (!map.has(act)) map.set(act, []);
    map.get(act)!.push(node);
  }
  return Array.from(map.entries());
}

function CharacterGraph({ characters }: { characters: any[] }) {
  if (characters.length === 0) return <div style={{ color: colors.muted, textAlign: "center", padding: space[8] }}>暂无角色数据</div>;
  const cx = 200, cy = 150, r = 120;
  const mainChar = characters[0];
  const others = characters.slice(1);
  return (
    <svg viewBox="0 0 400 300" width="100%" height="300">
      {/* Lines from main to others */}
      {others.map((_: any, i: number) => {
        const angle = (i / others.length) * 2 * Math.PI - Math.PI / 2;
        const x = cx + r * Math.cos(angle);
        const y = cy + r * Math.sin(angle);
        return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke={colors.border} strokeWidth={2} />;
      })}
      {/* Main character */}
      <circle cx={cx} cy={cy} r={35} fill={colors.accentBg} stroke={colors.accent} strokeWidth={2} />
      <text x={cx} y={cy + 4} textAnchor="middle" fontSize={13} fill={colors.fg} fontWeight={600}>{mainChar.name}</text>
      {/* Other characters */}
      {others.map((c: any, i: number) => {
        const angle = (i / others.length) * 2 * Math.PI - Math.PI / 2;
        const x = cx + r * Math.cos(angle);
        const y = cy + r * Math.sin(angle);
        return (
          <g key={i}>
            <circle cx={x} cy={y} r={25} fill={colors.surface} stroke={colors.border} strokeWidth={2} />
            <text x={x} y={y + 4} textAnchor="middle" fontSize={11} fill={colors.fgSecondary}>{c.name}</text>
          </g>
        );
      })}
    </svg>
  );
}

const style: Record<string, React.CSSProperties> = {
  layout: { display: "grid", gridTemplateColumns: "260px 1fr", gap: 0, minHeight: "100vh" },
  centered: { display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: space[16], color: colors.muted },
  sidebar: { borderRight: `1px solid ${colors.border}`, padding: "24px 0", background: colors.surface, overflowY: "auto", maxHeight: "100vh", position: "sticky", top: 0 },
  sidebarHeader: { padding: "0 20px 16px", borderBottom: `1px solid ${colors.borderLight}`, marginBottom: 8 },
  backLink: { color: colors.muted, fontSize: 12, textDecoration: "none" },
  sidebarTitle: { fontFamily: fonts.display, fontSize: 15, fontWeight: 600, color: colors.fg, marginTop: 8 },
  chapterCount: { fontSize: 12, color: colors.muted, marginTop: 4 },
  chapterList: { display: "flex", flexDirection: "column" },
  chapterItem: { display: "flex", alignItems: "center", gap: 10, padding: "10px 20px", fontSize: 13, cursor: "pointer", background: "none", border: "none", textAlign: "left", width: "100%", transition: "all 0.15s", borderLeft: "3px solid transparent" },
  chapterItemActive: { background: colors.accentBg, borderLeftColor: colors.accent, color: colors.accent, fontWeight: 500 },
  chapterNum: { fontFamily: fonts.mono, fontSize: 11, color: colors.muted, minWidth: 24 },
  chapterTitle: { flex: 1 },
  chapterDot: { width: 6, height: 6, borderRadius: "50%", marginLeft: "auto", flexShrink: 0 },
  main: { minWidth: 0 },
  tabs: { display: "flex", gap: 0, borderBottom: `1px solid ${colors.border}`, padding: "0 24px", background: colors.surface },
  tab: { padding: "14px 18px", fontSize: 13, fontWeight: 500, color: colors.muted, borderBottom: "2px solid transparent", background: "none", border: "none", cursor: "pointer", transition: "all 0.15s" },
  tabActive: { color: colors.accent, borderBottomColor: colors.accent },
  readingPanel: { background: colors.bg, minHeight: "calc(100vh - 140px)" },
  readingArea: { maxWidth: 680, margin: "0 auto", padding: "40px 32px 60px", fontSize: 17, lineHeight: 2, color: colors.fg, overflow: "auto", maxHeight: "calc(100vh - 140px)" },
  chapterHeader: { textAlign: "center", marginBottom: 40, paddingBottom: 24, borderBottom: `1px solid ${colors.borderLight}` },
  chapterH2: { fontFamily: fonts.display, fontSize: 24, fontWeight: 700, marginBottom: 8, color: colors.fg },
  chapterMeta: { fontSize: 13, color: colors.muted },
  readingText: { textAlign: "justify" },
  vizPanel: { padding: "24px 32px", minHeight: "calc(100vh - 140px)" },
  vizGrid: { display: "grid", gridTemplateColumns: "280px 1fr", gap: 32, maxWidth: 900, margin: "0 auto" },
  vizTitle: { fontFamily: fonts.display, fontSize: 16, fontWeight: 600, color: colors.fg, marginBottom: 16 },
  chartWrap: { display: "flex", alignItems: "center", justifyContent: "center" },
  qualityList: { display: "flex", flexDirection: "column", gap: 16 },
  qualityItem: { padding: "12px 16px", background: colors.surface, borderRadius: radius.sm, border: `1px solid ${colors.border}` },
  qualityHeader: { display: "flex", alignItems: "center", gap: 8, marginBottom: 8 },
  charGrid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 32, maxWidth: 1000, margin: "0 auto" },
  characterCards: { display: "flex", flexDirection: "column", gap: 16 },
  charCard: { padding: 16, background: colors.surface, borderRadius: radius.md, border: `1px solid ${colors.border}` },
};
