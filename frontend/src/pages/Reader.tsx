import { useState, useEffect, useCallback, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { api, type ChapterInfo, type ChapterDetail, type StoryDetail } from "../services/api";
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from "recharts";
import { colors, fonts, radius, space, shadows } from "../styles";
import TabPanel from "../components/TabPanel";
import CharacterGraph from "../components/CharacterGraph";

const LS_PROGRESS_KEY = "reader-progress";

function loadProgress(storyId: string): { chapterNumber: number; scrollPct: number } | null {
  try { const raw = localStorage.getItem(`${LS_PROGRESS_KEY}-${storyId}`); return raw ? JSON.parse(raw) : null; }
  catch { return null; }
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
];

export default function Reader() {
  const { id } = useParams<{ id: string }>();
  const [story, setStory] = useState<StoryDetail | null>(null);
  const [chapters, setChapters] = useState<ChapterInfo[]>([]);
  const [selectedChapter, setSelectedChapter] = useState<ChapterDetail | null>(null);
  const [activeTab, setActiveTab] = useState("reading");
  const [loading, setLoading] = useState(true);
  const [chapterLoading, setChapterLoading] = useState(false);
  const [error, setError] = useState("");
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    Promise.all([api.getStory(id), api.listChapters(id)])
      .then(([s, c]) => { setStory(s); setChapters(c); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    if (!id || chapters.length === 0) return;
    const progress = loadProgress(id);
    if (progress) loadChapter(progress.chapterNumber);
  }, [id, chapters]);

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
    try { setSelectedChapter(await api.getChapter(id, num)); }
    catch (e) { setError(e instanceof Error ? e.message : "加载章节失败"); }
    finally { setChapterLoading(false); }
  }, [id]);

  if (loading) return <div style={s.centered}>加载中...</div>;
  if (error && !story) return <div style={{ ...s.centered, color: colors.danger }}>{error}</div>;
  if (!story) return <div style={s.centered}>故事不存在</div>;

  return (
    <div style={s.layout}>
      <aside style={s.sidebar}>
        <div style={s.sidebarHeader}>
          <Link to={`/story/${id}`} style={s.backLink}>&larr; 返回详情</Link>
          <div style={s.sidebarTitle}>章节目录</div>
          <div style={s.chapterCount}>{chapters.length} 章</div>
        </div>
        <div style={s.chapterList}>
          {chapters.map((ch) => (
            <button key={ch.chapter_number} onClick={() => loadChapter(ch.chapter_number)}
              style={{ ...s.chapterItem, ...(selectedChapter?.chapter_number === ch.chapter_number ? s.chapterItemActive : {}) }}>
              <span style={s.chapterNum}>{String(ch.chapter_number).padStart(2, "0")}</span>
              <span style={s.chapterTitle}>{ch.title}</span>
              <span style={{ ...s.chapterDot, background: ch.status === "published" || ch.status === "accepted" ? colors.success : ch.status === "draft" ? colors.warning : colors.border }} />
            </button>
          ))}
        </div>
      </aside>

      <main style={s.main}>
        <TabPanel tabs={tabDefs} activeTab={activeTab} onTabChange={setActiveTab} />

        {activeTab === "reading" && (
          <div style={s.readingPanel}>
            {chapterLoading ? <div style={s.centered}>加载中...</div> :
            selectedChapter ? (
              <div ref={contentRef} style={s.readingArea}>
                <div style={s.chapterHeader}>
                  <h2 style={s.chapterH2}>第{selectedChapter.chapter_number}章 · {selectedChapter.title}</h2>
                  <div style={s.chapterMeta}>
                    {selectedChapter.content.replace(/\s/g, "").length} 字
                    {selectedChapter.rewrites_count > 0 && ` · 已改写${selectedChapter.rewrites_count}次`}
                  </div>
                </div>
                <div style={s.readingText}>
                  {selectedChapter.content.split("\n\n").map((para, i) => (
                    <p key={i} style={{ marginBottom: "1.8em", textIndent: "2em" }}>{para}</p>
                  ))}
                </div>
              </div>
            ) : <div style={s.centered}>选择左侧章节开始阅读</div>}
          </div>
        )}

        {activeTab === "quality" && selectedChapter && <QualityTab chapter={selectedChapter} />}
        {activeTab === "emotion" && selectedChapter && <EmotionTab chapter={selectedChapter} />}
        {activeTab === "characters" && story && <CharactersTab story={story} />}
        {activeTab === "outline" && story && <OutlineTab story={story} chapters={chapters} />}
      </main>
    </div>
  );
}

function QualityTab({ chapter }: { chapter: ChapterDetail }) {
  return (
    <div style={s.vizPanel}>
      <div style={s.vizGrid}>
        <div style={s.chartWrap}>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={(chapter.check_results || []).map((cr) => ({
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
        <div style={s.qualityList}>
          <h3 style={s.vizTitle}>质量检测详情</h3>
          {(chapter.check_results || []).map((cr, i) => (
            <div key={i} style={s.qualityItem}>
              <div style={s.qualityHeader}>
                <span style={{ color: cr.passed ? colors.success : colors.danger, fontWeight: 700, fontSize: 14 }}>{cr.passed ? "\u2713" : "\u2717"}</span>
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
  );
}

function EmotionTab({ chapter }: { chapter: ChapterDetail }) {
  return (
    <div style={s.vizPanel}>
      <div style={s.vizTitle}>情绪曲线</div>
      {chapter.emotion_curve?.length > 0 ? (
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={chapter.emotion_curve.map((p) => ({ pos: p.position_pct, tension: p.tension, relaxation: p.relaxation, sadness: p.sadness, pleasure: p.pleasure }))}>
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
  );
}

function CharactersTab({ story }: { story: StoryDetail }) {
  return (
    <div style={s.vizPanel}>
      <div style={s.charGrid}>
        <div style={s.chartWrap}>
          <CharacterGraph characters={story.characters || []} />
        </div>
        <div style={s.characterCards}>
          <h3 style={s.vizTitle}>角色信息</h3>
          {(story.characters || []).map((c, i) => (
            <div key={i} style={s.charCard}>
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
  );
}

function OutlineTab({ story, chapters }: { story: StoryDetail; chapters: ChapterInfo[] }) {
  return (
    <div style={s.vizPanel}>
      <h3 style={{ ...s.vizTitle, textAlign: "center" }}>故事大纲</h3>
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

const s: Record<string, React.CSSProperties> = {
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
