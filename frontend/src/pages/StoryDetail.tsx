import { useEffect, useState, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { api, ChapterInfo, ChapterDetail, type StoryDetail as StoryDetailType } from "../services/api";
import { useGeneration } from "../GenerationContext";
import { colors, space, font, btn, card, badge, layout, section } from "../styles";

type Tab = "chapters" | "outline" | "world" | "foreshadowing";

const severityColors: Record<string, string> = {
  critical: colors.danger,
  high: "#f97316",
  medium: "#eab308",
  low: colors.textMuted,
};

const severityBg: Record<string, string> = {
  critical: colors.dangerBg,
  high: "rgba(249,115,22,0.12)",
  medium: "rgba(234,179,8,0.12)",
  low: "rgba(113,113,122,0.1)",
};

export default function StoryDetail() {
  const { id } = useParams<{ id: string }>();
  const { getGeneration, isGenerating, startGeneration, cancelGeneration } = useGeneration();
  const [story, setStory] = useState<StoryDetailType | null>(null);
  const [chapters, setChapters] = useState<ChapterInfo[]>([]);
  const [activeTab, setActiveTab] = useState<Tab>("chapters");
  const [selectedChapter, setSelectedChapter] = useState<ChapterDetail | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  // Write-all state
  const [writingAll, setWritingAll] = useState(false);
  const [writeAllProgress, setWriteAllProgress] = useState({ current: 0, target: 0 });
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Rewrite state
  const [rewriting, setRewriting] = useState(false);

  // Focus mode
  const [focusMode, setFocusMode] = useState(false);

  // 从全局 context 读取当前故事的生成状态
  const gen = id ? getGeneration(id) : undefined;
  const streaming = id ? isGenerating(id) : false;

  // 当生成完成时，自动刷新章节列表
  const prevGenStatusRef = useRef<string>("");
  useEffect(() => {
    if (!id || !gen) return;
    if (prevGenStatusRef.current !== "complete" && gen.status === "complete") {
      api.listChapters(id).then(setChapters);
      api.getStory(id).then((s) => setStory(s));
      // 自动选中新章节
      setTimeout(() => loadChapter(gen.chapterNumber), 500);
    }
    prevGenStatusRef.current = gen.status;
  }, [id, gen?.status]);

  useEffect(() => {
    if (!id) return;
    Promise.all([api.getStory(id), api.listChapters(id)])
      .then(([s, c]) => { setStory(s); setChapters(c); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [id]);

  const loadChapter = async (num: number) => {
    if (!id) return;
    setSelectedChapter(null);
    try {
      setSelectedChapter(await api.getChapter(id, num));
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载章节失败");
    }
  };

  // === 全局 SSE 生成 — 切换页面不会断 ===
  const handleWriteNext = () => {
    if (!id || streaming) return;
    setError("");
    startGeneration(id, (story?.current_chapter || 0) + 1);
  };

  const handleCancel = () => {
    if (!id) return;
    cancelGeneration(id);
  };

  // === Blocking write (fallback) ===
  const [blockingWrite, setBlockingWrite] = useState(false);
  const writeNextBlocking = async () => {
    if (!id || streaming || blockingWrite) return;
    setBlockingWrite(true);
    setError("");
    try {
      const ch = await api.writeNext(id);
      setChapters((prev) => [...prev, {
        chapter_number: ch.chapter_number, title: ch.title,
        word_count: ch.word_count, status: ch.status,
        alignment_score: 0, originality_score: 0, rewrites_count: ch.rewrites_count,
      }]);
      setStory((prev) => prev ? { ...prev, current_chapter: ch.chapter_number } : prev);
      loadChapter(ch.chapter_number);
    } catch (e) {
      setError(e instanceof Error ? e.message : "写作失败");
    } finally {
      setBlockingWrite(false);
    }
  };

  // === Write All ===
  const writeAll = async () => {
    if (!id || writingAll || streaming) return;
    setWritingAll(true);
    setError("");
    const target = story?.config?.target_chapters || 0;
    const current = story?.current_chapter || 0;
    setWriteAllProgress({ current, target });

    // Poll chapters every 2s
    pollRef.current = setInterval(async () => {
      try {
        const chs = await api.listChapters(id);
        setWriteAllProgress({ current: chs.length, target });
      } catch {}
    }, 2000);

    try {
      await api.writeAll(id, current + 1);
      const newChapters = await api.listChapters(id);
      setChapters(newChapters);
      setStory((prev) => prev ? { ...prev, current_chapter: newChapters.length } : prev);
    } catch (e) {
      setError(e instanceof Error ? e.message : "批量写作失败");
    } finally {
      if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
      setWritingAll(false);
    }
  };

  // === Rewrite ===
  const rewriteChapter = async () => {
    if (!id || !selectedChapter || rewriting) return;
    setRewriting(true);
    setError("");
    try {
      const result = await api.rewriteChapter(id, selectedChapter.chapter_number);
      await loadChapter(selectedChapter.chapter_number);
      setError(`重写完成，修复 ${result.issues_found} 个问题`);
      setTimeout(() => setError(""), 3000);
    } catch (e) {
      setError(e instanceof Error ? e.message : "重写失败");
    } finally {
      setRewriting(false);
    }
  };

  // === Render ===
  if (loading) return <div style={layout.centered}>加载中...</div>;
  if (error && !story) return <div style={{ ...layout.centered, color: colors.danger }}>{error}</div>;
  if (!story) return <div style={{ ...layout.centered, color: colors.danger }}>故事不存在</div>;

  const cfg = story.config || {};
  const progressPct = cfg.target_chapters ? (story.current_chapter / cfg.target_chapters) * 100 : 0;

  const tabLabels: Record<Tab, string> = { chapters: "章节列表", outline: "大纲", world: "世界观", foreshadowing: "伏笔" };

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: space[6] }}>
        <Link to="/" style={{ color: colors.textMuted, fontSize: "13px", textDecoration: "none" }}>&larr; 返回</Link>
        <h1 style={{ ...font["2xl"], margin: "8px 0 4px", fontWeight: 700 }}>{cfg.title || "未命名"}</h1>
        <div style={{ ...font.sm, color: colors.textMuted }}>
          {cfg.genre} &middot; {cfg.style} &middot; {cfg.pov} &middot; {story.current_chapter}/{cfg.target_chapters} 章
        </div>
        {/* Progress bar */}
        <div style={{ marginTop: space[3], height: "4px", background: colors.bgElevated, borderRadius: "2px" }}>
          <div style={{ height: "100%", width: `${progressPct}%`, background: colors.primary, borderRadius: "2px", transition: "width 0.3s" }} />
        </div>
      </div>

      {/* Error / Status */}
      {error && (
        <div style={{ padding: `${space[2]} ${space[4]}`, marginBottom: space[3], borderRadius: "6px", fontSize: "13px",
          background: error.startsWith("重写完成") ? "rgba(34,197,94,0.12)" : colors.dangerBg,
          color: error.startsWith("重写完成") ? colors.primary : colors.danger,
        }}>{error}</div>
      )}

      {/* Streaming status bar — 从全局 context 读取，切换页面不会丢 */}
      {gen && gen.status !== "idle" && gen.status !== "complete" && gen.status !== "error" && (
        <div style={{ ...card, marginBottom: space[4], padding: `${space[3]} ${space[4]}`,
          display: "flex", alignItems: "center", justifyContent: "space-between",
          borderColor: colors.primaryBorder, background: colors.primaryMuted }}>
          <div style={{ display: "flex", alignItems: "center", gap: space[3] }}>
            <style>{`@keyframes streamPulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } } @keyframes progressGlow { 0% { box-shadow: 0 0 4px ${colors.primary}; } 50% { box-shadow: 0 0 12px ${colors.primary}; } 100% { box-shadow: 0 0 4px ${colors.primary}; } }`}</style>
            <span style={{ animation: "spin 1s linear infinite, streamPulse 1.5s ease-in-out infinite", fontSize: "16px" }}>&#9696;</span>
            <span style={{ ...font.sm, fontWeight: 600, color: colors.primary }}>
              第{gen.chapterNumber}章 &middot; {
                gen.status === "generating" ? "正在生成..." :
                gen.status === "checking" ? "质检中..." :
                gen.status === "rewriting" ? "改写中..." :
                gen.status === "saving" ? "保存中..." : gen.status
              }
            </span>
            {gen.tokensReceived > 0 && (
              <span style={{ ...font.xs, color: colors.textMuted }}>({gen.tokensReceived} tokens)</span>
            )}
            <div style={{
              width: "80px", height: "4px", background: colors.bgElevated,
              borderRadius: "2px", overflow: "hidden", marginLeft: space[2],
            }}>
              <div style={{
                height: "100%", width: "30%", background: colors.primary,
                borderRadius: "2px", animation: "progressGlow 1.5s ease-in-out infinite",
              }} />
            </div>
          </div>
          <button onClick={handleCancel} style={{ ...btn.ghost, padding: `${space[1]} ${space[3]}`, fontSize: "12px" }}>
            取消
          </button>
        </div>
      )}

      {/* 生成错误 */}
      {gen && gen.status === "error" && (
        <div style={{ padding: `${space[2]} ${space[4]}`, marginBottom: space[3], borderRadius: "6px", fontSize: "13px",
          background: colors.dangerBg, color: colors.danger }}>
          生成失败：{gen.errorMessage}
        </div>
      )}

      {/* Write-all progress */}
      {writingAll && (
        <div style={{ ...card, marginBottom: space[4], padding: `${space[3]} ${space[4]}`, borderColor: colors.warningBorder, background: colors.warningBg }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: space[2], ...font.sm }}>
            <span style={{ fontWeight: 600, color: colors.warning }}>自动写作中...</span>
            <span style={{ color: colors.warning }}>{writeAllProgress.current}/{writeAllProgress.target} 章</span>
          </div>
          <div style={{ height: "4px", background: "rgba(245,158,11,0.15)", borderRadius: "2px" }}>
            <div style={{ height: "100%", width: `${writeAllProgress.target > 0 ? (writeAllProgress.current / writeAllProgress.target) * 100 : 0}%`,
              background: colors.warning, borderRadius: "2px", transition: "width 0.5s" }} />
          </div>
        </div>
      )}

      {/* Action buttons */}
      <div style={{ display: "flex", gap: space[3], marginBottom: space[5], flexWrap: "wrap" }}>
        <button onClick={handleWriteNext} disabled={streaming || writingAll}
          style={{ ...btn.primary, opacity: streaming || writingAll ? 0.6 : 1 }}>
          {streaming ? "生成中..." : "流式写下一章"}
        </button>
        <button onClick={writeNextBlocking} disabled={streaming || writingAll || blockingWrite}
          style={{ ...btn.ghost, opacity: streaming || writingAll || blockingWrite ? 0.6 : 1 }}>
          {blockingWrite ? "生成中..." : "同步写下一章"}
        </button>
        <button onClick={writeAll} disabled={writingAll || streaming}
          style={{ ...btn.warning, opacity: writingAll || streaming ? 0.6 : 1 }}>
          {writingAll ? "自动写作中..." : "写完剩余章节"}
        </button>
      </div>

      {/* Streaming live preview — 从全局 context 读取 */}
      {gen && gen.contentChunks.length > 0 && (
        <div style={{ ...card, marginBottom: space[5], padding: space[5],
          maxHeight: "400px", overflow: "auto", whiteSpace: "pre-wrap" as const,
          fontSize: "14px", lineHeight: "1.9", color: "#d0d0d0", fontFamily: "inherit" }}>
          {gen.contentChunks.join("")}
          {streaming && <span style={{ animation: "blink 0.8s infinite", color: colors.primary }}>&#9608;</span>}
          <div style={{ ...font.xs, color: colors.textMuted, marginTop: space[3], paddingTop: space[3], borderTop: `1px solid ${colors.border}` }}>
            <span>实时字数：{gen.contentChunks.join("").replace(/\s/g, "").length}</span>
            <span style={{ marginLeft: space[4] }}>预计阅读：{Math.ceil(gen.contentChunks.join("").replace(/\s/g, "").length / 300)} 分钟</span>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: "flex", gap: "4px", marginBottom: space[5], borderBottom: `1px solid ${colors.border}`, opacity: focusMode ? 0 : 1, transition: "opacity 0.2s" }}>
        {(["chapters", "outline", "world", "foreshadowing"] as Tab[]).map((tab) => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            style={{ padding: `${space[2]} ${space[4]}`, fontSize: "13px", background: "none", border: "none", cursor: "pointer",
              color: activeTab === tab ? colors.primary : colors.textMuted,
              borderBottom: activeTab === tab ? `2px solid ${colors.primary}` : "2px solid transparent",
              fontWeight: activeTab === tab ? 600 : 400 }}>
            {tabLabels[tab]}
          </button>
        ))}
        <div style={{ flex: 1 }} />
        <button onClick={() => setFocusMode(!focusMode)}
          style={{
            padding: `${space[1]} ${space[3]}`,
            fontSize: "12px",
            background: "none",
            border: `1px solid ${focusMode ? colors.primaryBorder : colors.border}`,
            borderRadius: "4px",
            cursor: "pointer",
            color: focusMode ? colors.primary : colors.textMuted,
            display: "flex",
            alignItems: "center",
            gap: space[1],
          }}>
          {focusMode ? "退出专注" : "专注模式"}
        </button>
      </div>

      {/* Chapters Tab */}
      {activeTab === "chapters" && (
        <div style={{ display: "flex", gap: space[5], opacity: focusMode ? 0.3 : 1, transition: "opacity 0.2s" }}>
          {/* Sidebar */}
          <div style={{
            width: focusMode ? "0" : "220px",
            flexShrink: 0,
            overflow: focusMode ? "hidden" : "auto",
            transition: "width 0.3s ease",
          }}>
            {chapters.length === 0 ? (
              <div style={{ color: colors.textDim, fontSize: "13px", padding: `${space[4]} 0` }}>暂无章节</div>
            ) : (
              chapters.map((ch) => (
                <button key={ch.chapter_number} onClick={() => loadChapter(ch.chapter_number)}
                  style={{
                    display: "block",
                    width: "100%",
                    textAlign: "left",
                    padding: `${space[2]} ${space[2]}`,
                    fontSize: "12px",
                    background: selectedChapter?.chapter_number === ch.chapter_number ? "rgba(34,197,94,0.1)" : "transparent",
                    border: "none",
                    borderRadius: "4px",
                    color: selectedChapter?.chapter_number === ch.chapter_number ? colors.primary : "#aaa",
                    cursor: "pointer",
                    marginBottom: "2px",
                    transition: "background 0.15s",
                  }}>
                  <span style={{ color: colors.primary, marginRight: "6px", fontWeight: 600 }}>第{ch.chapter_number}章</span>
                  <span style={{ fontSize: "11px", color: colors.textDim }}>{ch.word_count}字</span>
                </button>
              ))
            )}
          </div>

          {/* Content */}
          <div style={{
            flex: 1,
            minWidth: 0,
            maxWidth: focusMode ? "800px" : "100%",
            margin: focusMode ? "0 auto" : "0",
            transition: "max-width 0.3s ease, margin 0.3s ease",
          }}>
            {selectedChapter ? (
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: space[4] }}>
                  <h3 style={{ fontSize: "15px", color: colors.primary, margin: 0 }}>
                    第{selectedChapter.chapter_number}章 &middot; {selectedChapter.title}
                    <span style={{ marginLeft: space[3], fontSize: "12px", color: colors.textMuted, fontWeight: 400 }}>
                      {selectedChapter.content ? selectedChapter.content.replace(/\s/g, "").length : 0}字
                    </span>
                  </h3>
                  <button onClick={rewriteChapter} disabled={rewriting}
                    style={{ ...btn.ghost, padding: `${space[1]} ${space[3]}`, fontSize: "12px", opacity: rewriting ? 0.6 : 1 }}>
                    {rewriting ? "重写中..." : "重写本章"}
                  </button>
                </div>

                {/* Check results badges */}
                {(selectedChapter.check_results?.length > 0 || selectedChapter.rewrites_count > 0) && (
                  <div style={{ display: "flex", gap: space[1], marginBottom: space[4], flexWrap: "wrap" }}>
                    {selectedChapter.check_results?.map((cr, i) => (
                      <span key={i} style={{
                        padding: "2px 6px",
                        fontSize: "10px",
                        borderRadius: "3px",
                        background: cr.passed ? colors.primaryMuted : colors.dangerBg,
                        color: cr.passed ? colors.primary : colors.danger,
                        border: `1px solid ${cr.passed ? colors.primaryBorder : colors.dangerBorder}`,
                        fontWeight: 500,
                      }}>
                        {cr.layer} {cr.passed ? "\u2713" : "\u2717"}
                        {cr.issues_count > 0 && ` (${cr.issues_count})`}
                      </span>
                    ))}
                    {selectedChapter.rewrites_count > 0 && (
                      <span style={{
                        padding: "2px 6px",
                        fontSize: "10px",
                        borderRadius: "3px",
                        background: colors.warningBg,
                        color: colors.warning,
                        border: `1px solid ${colors.warningBorder}`,
                        fontWeight: 500,
                      }}>
                        已改写{selectedChapter.rewrites_count}次
                      </span>
                    )}
                  </div>
                )}

                {/* Quality check issues detail */}
                {selectedChapter.check_results?.some((cr) => cr.issues_count > 0) && (
                  <div style={{ ...card, marginBottom: space[4], padding: space[4] }}>
                    <div style={{ ...font.sm, fontWeight: 600, color: colors.textSecondary, marginBottom: space[3] }}>质检详情</div>
                    {selectedChapter.check_results.filter((cr) => cr.issues_count > 0).map((cr) => (
                      <div key={cr.layer} style={{ marginBottom: space[3] }}>
                        <div style={{ ...font.xs, fontWeight: 600, color: cr.passed ? colors.primary : colors.danger, marginBottom: space[1] }}>
                          [{cr.layer}] {cr.passed ? "通过" : "未通过"}
                          {cr.scores && Object.keys(cr.scores).length > 0 && (
                            <span style={{ color: colors.textMuted, fontWeight: 400 }}>
                              {" "}({Object.entries(cr.scores).map(([k, v]) => `${k}: ${typeof v === "number" ? v.toFixed(2) : v}`).join(", ")})
                            </span>
                          )}
                        </div>
                        {cr.issues?.map((issue: any, j: number) => (
                          <div key={j} style={{
                            padding: `${space[2]} ${space[3]}`, marginBottom: space[1], borderRadius: "4px",
                            background: severityBg[issue.severity] || "transparent",
                            border: `1px solid ${severityColors[issue.severity]}20`,
                          }}>
                            <div style={{ display: "flex", gap: space[2], alignItems: "center" }}>
                              <span style={{ padding: "1px 5px", fontSize: "10px", borderRadius: "3px",
                                background: severityColors[issue.severity], color: "#fff", fontWeight: 600 }}>
                                {issue.severity}
                              </span>
                              <span style={{ ...font.xs, color: colors.text }}>{issue.type}: {issue.description}</span>
                            </div>
                            {issue.suggestion && (
                              <div style={{ ...font.xs, color: colors.textMuted, marginTop: space[1], paddingLeft: space[6] }}>
                                建议: {issue.suggestion}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    ))}
                  </div>
                )}

                {/* Chapter text */}
                <div style={{
                  ...card,
                  padding: focusMode ? space[8] : space[6],
                  fontSize: focusMode ? "16px" : "15px",
                  lineHeight: focusMode ? "2.0" : "1.9",
                  whiteSpace: "pre-wrap" as const,
                  color: "#d0d0d0",
                  maxHeight: focusMode ? "85vh" : "70vh",
                  overflow: "auto",
                  position: "relative",
                  boxShadow: focusMode ? "inset 0 0 100px rgba(0,0,0,0.3)" : "none",
                  transition: "all 0.3s ease",
                }}>
                  {selectedChapter.content || "暂无内容"}
                </div>
                {focusMode && (
                  <div style={{
                    position: "fixed",
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    pointerEvents: "none",
                    background: "radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.4) 100%)",
                    zIndex: -1,
                  }} />
                )}
              </div>
            ) : (
              <div style={layout.centered}>
                {chapters.length === 0 ? "点击上方按钮开始写作" : "选择左侧章节查看内容"}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Outline Tab */}
      {activeTab === "outline" && (
        <div style={{ display: "flex", flexDirection: "column", gap: space[2] }}>
          {(story.outline || []).map((node) => (
            <div key={node.chapter} style={{ ...card, padding: `${space[3]} ${space[4]}`, fontSize: "13px" }}>
              <div style={{ fontWeight: 600, color: colors.primary, marginBottom: space[1] }}>
                第{node.chapter}章 &middot; {node.title}
                {node.act && <span style={{ marginLeft: space[2], fontSize: "11px", color: colors.textMuted }}>[{node.act}]</span>}
              </div>
              <div style={{ color: "#bbb", marginBottom: space[1] }}>{node.goal}</div>
              <div style={{ color: colors.textMuted }}>
                情绪：{node.emotional_beat}
                {node.twist_note && " &middot; 转折：" + node.twist_note}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* World Tab */}
      {activeTab === "world" && (
        <div>
          <Section title="世界观设定">{story.world_bible?.setting || "待生成"}</Section>
          <Section title="世界规则">
            <ul style={{ color: "#bbb", lineHeight: "2", paddingLeft: space[5] }}>
              {(story.world_bible?.rules || []).map((r, i) => <li key={i}>{r}</li>)}
              {!story.world_bible?.rules?.length && <li style={{ color: colors.textDim }}>无</li>}
            </ul>
          </Section>
          <Section title="势力">
            <div style={{ display: "flex", flexWrap: "wrap", gap: space[2] }}>
              {(story.world_bible?.factions || []).map((f, i) => (
                <span key={i} style={{ padding: `${space[1]} ${space[3]}`, background: colors.bgElevated, borderRadius: "4px", fontSize: "13px", color: "#ccc" }}>{f}</span>
              ))}
            </div>
          </Section>
          <Section title="角色">
            <div style={{ display: "flex", flexDirection: "column", gap: space[2] }}>
              {(story.characters || []).map((c, i) => (
                <div key={i} style={{ ...card, padding: space[3] }}>
                  <div style={{ fontWeight: 600, color: colors.primary }}>{c.name} ({c.role})</div>
                  <div style={{ fontSize: "13px", color: "#aaa", marginTop: space[1] }}>{c.traits || c.personality}</div>
                  <div style={{ fontSize: "12px", color: colors.textMuted, marginTop: space[1] }}>{c.arc}</div>
                </div>
              ))}
            </div>
          </Section>
        </div>
      )}

      {/* Foreshadowing Tab */}
      {activeTab === "foreshadowing" && (
        <div style={{ display: "flex", flexDirection: "column", gap: space[2] }}>
          {(!story.foreshadowing_list || story.foreshadowing_list.length === 0) ? (
            <div style={{ color: colors.textDim, padding: space[5], textAlign: "center" }}>暂无伏笔记录</div>
          ) : (
            story.foreshadowing_list.map((fs) => {
              const statusStyle = fs.status === "resolved"
                ? { bg: colors.primaryMuted, color: colors.primary, border: colors.primaryBorder }
                : fs.status === "abandoned"
                ? { bg: "rgba(113,113,122,0.1)", color: colors.textDim, border: `1px solid ${colors.border}` }
                : { bg: colors.warningBg, color: colors.warning, border: colors.warningBorder };
              return (
                <div key={fs.id} style={{ ...card, padding: `${space[3]} ${space[4]}` }}>
                  <div style={{ display: "flex", alignItems: "center", gap: space[3], marginBottom: space[1] }}>
                    <span style={{ padding: "2px 8px", fontSize: "11px", borderRadius: "4px", fontWeight: 600,
                      background: statusStyle.bg, color: statusStyle.color, border: `1px solid ${statusStyle.border}` }}>
                      {fs.status === "resolved" ? "已回收" : fs.status === "abandoned" ? "已废弃" : "待回收"}
                    </span>
                    <span style={{ ...font.sm, color: colors.text }}>{fs.description}</span>
                  </div>
                  <div style={{ ...font.xs, color: colors.textMuted }}>
                    埋设: 第{fs.planted_chapter}章
                    {fs.payoff_chapter && ` · 回收: 第${fs.payoff_chapter}章`}
                    {fs.min_payoff_chapter && fs.status === "unresolved" && ` · 最早第${fs.min_payoff_chapter}章回收`}
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}

      {/* Blink animation for streaming cursor */}
      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } } @keyframes blink { 0%,100% { opacity:1; } 50% { opacity:0; } }`}</style>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: space[6] }}>
      <h3 style={{ ...font.md, fontWeight: 600, color: colors.primary, marginBottom: space[2] }}>{title}</h3>
      <div style={{ color: "#bbb", lineHeight: "1.8", fontSize: "14px" }}>{children}</div>
    </div>
  );
}
