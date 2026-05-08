import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { colors, space, font, btn, layout, genreColors } from "../styles";
import { api, StoryConfig } from "../services/api";
import TagGroup from "../components/TagGroup";
import Stepper from "../components/Stepper";

const GENRE_OPTIONS = ["仙侠", "玄幻", "都市", "言情", "悬疑", "科幻", "历史", "武侠", "游戏", "奇幻", "其他"];
const STYLE_OPTIONS = ["轻松幽默", "严肃文学", "爽文快节奏", "文青细腻", "悬疑紧绷", "热血战斗", "虐心催泪", "甜宠治愈"];
const POV_OPTIONS = ["第一人称", "第三人称有限", "第三人称全知"];

const s = {
  layout: { display: "grid", gridTemplateColumns: "1fr 360px", gap: "36px", alignItems: "start" },
  formSection: { background: colors.surfaceRaised, border: "1px solid " + colors.border, borderRadius: "10px", padding: "24px", marginBottom: "20px" },
  formSectionTitle: { fontFamily: "'Noto Serif SC','Songti SC','STSong',Georgia,serif", fontSize: "16px", fontWeight: 600, marginBottom: "16px" },
  formGroup: { marginBottom: "16px" },
  formGroupLast: { marginBottom: "0" },
  formLabel: { display: "block", fontSize: "13px", fontWeight: 500, color: colors.fgSecondary, marginBottom: "6px" },
  formInput: { width: "100%", padding: "10px 14px", border: "1px solid " + colors.border, borderRadius: "6px", background: colors.surface, fontSize: "14px", fontFamily: "inherit", color: colors.fg },
  formTextarea: { width: "100%", padding: "10px 14px", border: "1px solid " + colors.border, borderRadius: "6px", background: colors.surface, fontSize: "14px", fontFamily: "inherit", color: colors.fg, resize: "vertical" as const, minHeight: "80px", lineHeight: "1.6" },
  tagSelector: { display: "flex", flexWrap: "wrap" as const, gap: "8px" },
  tagOption: { padding: "6px 14px", border: "1px solid " + colors.border, borderRadius: "20px", fontSize: "13px", cursor: "pointer", background: "transparent", color: colors.muted },
  tagOptionSelected: { padding: "6px 14px", border: "1px solid " + colors.accent, borderRadius: "20px", fontSize: "13px", cursor: "pointer", background: colors.accent, color: "#fff" },
  stepper: { display: "flex", alignItems: "center", gap: "12px" },
  stepperBtn: { width: "32px", height: "32px", border: "1px solid " + colors.border, borderRadius: "6px", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", background: colors.surface, color: colors.fg, fontSize: "16px" },
  stepperValue: { minWidth: "60px", textAlign: "center" as const, fontSize: "15px", fontWeight: 500 },
  previewCard: { position: "sticky" as const, top: "40px", background: colors.surfaceRaised, border: "1px solid " + colors.border, borderRadius: "10px", overflow: "hidden" },
  previewStrip: { height: "4px" },
  previewBody: { padding: "24px" },
  previewLabel: { fontSize: "11px", textTransform: "uppercase" as const, letterSpacing: "0.08em", color: colors.muted, marginBottom: "16px" },
  previewTitle: { fontFamily: "'Noto Serif SC','Songti SC','STSong',Georgia,serif", fontSize: "22px", fontWeight: 700, marginBottom: "8px" },
  previewTheme: { fontSize: "13px", color: colors.muted, lineHeight: 1.6, marginBottom: "20px", minHeight: "42px" },
  previewMeta: { display: "flex", flexWrap: "wrap" as const, gap: "8px", marginBottom: "20px" },
  cardBadge: { padding: "4px 10px", borderRadius: "12px", fontSize: "12px", background: colors.accentBg, color: colors.accent, fontWeight: 500 },
  previewStats: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", paddingTop: "16px", borderTop: "1px solid " + colors.borderLight },
  previewStat: {},
  previewStatLabel: { fontSize: "11px", color: colors.muted, display: "block" },
  previewStatValue: { fontSize: "15px", fontWeight: 500 },
  aiGenerateBtn: { width: "100%", padding: "12px 20px", background: colors.accent, color: "#fff", border: "none", borderRadius: "6px", fontSize: "14px", fontWeight: 600, cursor: "pointer", marginTop: "12px" },
  submitBtn: { width: "100%", padding: "14px 24px", background: colors.primary, color: "#fff", border: "none", borderRadius: "6px", fontSize: "15px", fontWeight: 600, cursor: "pointer", marginTop: "24px" },
};
const PreviewCard: React.FC<{ config: StoryConfig }> = ({ config }) => {
  const totalWords = config.target_chapters * config.words_per_chapter;
  const estimatedMinutes = Math.ceil(totalWords / 150);
const genreColorMap: Record<string, string> = {
    "仙侠": genreColors.xiuxian, "玄幻": genreColors.xuanhui, "都市": genreColors.dushi,
    "科幻": genreColors.kehuan, "言情": genreColors.lingyi, "悬疑": genreColors.xuanhui,
    "历史": genreColors.lishi, "武侠": genreColors.wuxia, "游戏": genreColors.youxi,
    "奇幻": genreColors.qihuan, "其他": genreColors.qihuan,
  };
  const genreColor = genreColorMap[config.genre || "其他"] || genreColors.qihuan;

  return (
    <div style={s.previewCard}>
      <div style={{ ...s.previewStrip, background: genreColor }} />
      <div style={s.previewBody}>
<div style={s.previewLabel}>实时预览</div>
        <div style={s.previewTitle}>{config.title || "未命名作品"}</div>
        <div style={s.previewTheme}>{config.theme || "等待你输入灵感……"}</div>
        <div style={s.previewMeta}>
          {config.genre && <span style={s.cardBadge}>{config.genre}</span>}
          {config.pov && <span style={s.cardBadge}>{config.pov}</span>}
        </div>
<div style={s.previewStats}>
          <div style={s.previewStat}><label style={s.previewStatLabel}>目标章数</label><span style={s.previewStatValue}>{config.target_chapters} 章</span></div>
          <div style={s.previewStat}><label style={s.previewStatLabel}>每章字数</label><span style={s.previewStatValue}>{config.words_per_chapter.toLocaleString()} 字</span></div>
          <div style={s.previewStat}><label style={s.previewStatLabel}>总字数</label><span style={s.previewStatValue}>{totalWords.toLocaleString()} 字</span></div>
          <div style={s.previewStat}><label style={s.previewStatLabel}>预计时长</label><span style={s.previewStatValue}>~{estimatedMinutes} 分钟</span></div>
        </div>
      </div>
    </div>
  );
};

const ErrorBanner: React.FC<{ message: string; onDismiss: () => void }> = ({ message, onDismiss }) => (
  <div style={{ background: colors.dangerMuted, border: "1px solid " + colors.dangerBorder, borderRadius: "8px", padding: space[3] + " " + space[4], display: "flex", alignItems: "center", justifyContent: "space-between", gap: space[3], marginBottom: space[4] }}>
    <div style={{ display: "flex", alignItems: "center", gap: space[3] }}>
      <svg width="16" height="16" viewBox="0 0 16 16" fill={colors.danger}><path d="M8 1.5a6.5 6.5 0 100 13 6.5 6.5 0 000-13zM7 5a1 1 0 112 0v3a1 1 0 11-2 0V5zm1 7a1 1 0 100-2 1 1 0 000 2z" /></svg>
      <span style={{ ...font.sm, color: colors.danger }}>{message}</span>
    </div>
    <button onClick={onDismiss} style={{ ...btn.icon, color: colors.danger }}>
      <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor"><path d="M1 1l12 12M13 1L1 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /></svg>
    </button>
  </div>
);

export default function StoryCreate() {
  const navigate = useNavigate();
  const [idea, setIdea] = useState("");
  const [form, setForm] = useState<StoryConfig>({
    title: "", genre: "仙侠", style: "爽文快节奏", pov: "第三人称",
    target_chapters: 20, words_per_chapter: 3000, target_audience: "", theme: "",
  });
  const [generating, setGenerating] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

const handleGenerate = async () => {
    if (!idea.trim()) { setError("请先输入创作灵感"); return; }
    setError(null); setGenerating(true);
    try { const meta = await api.generateMeta(idea.trim(), form.genre); setForm((f) => ({ ...f, title: meta.title, theme: meta.theme })); }
    catch { setError("生成失败，请重试或手动输入"); }
    finally { setGenerating(false); }
  };

const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setError(null);
    if (!form.title.trim()) { setError("请先生成或输入小说标题"); return; }
    setLoading(true);
    try { const res = await api.createStory(form); navigate("/story/" + res.id); }
    catch (err) { setError(err instanceof Error ? err.message : "创建失败，请重试"); }
    finally { setLoading(false); }
  };

return (
    <div style={{ ...layout.page, padding: space[6] + " " + space[8], background: colors.surface, minHeight: "100vh" }}>
      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}
      <div style={s.layout}>
        <div className="create-form">
          <div style={s.formSection}>
            <div style={s.formSectionTitle}>灵感火花</div>
            <div style={s.formGroup}>
              <label style={s.formLabel}>用一句话描述你的想法</label>
              <textarea style={s.formTextarea} placeholder="比如：一个修仙者发现自己修炼的灵气其实是外星文明的实验数据……" value={idea} onChange={(e) => setIdea(e.target.value)} />
            </div>
            <button style={s.aiGenerateBtn} onClick={handleGenerate} disabled={generating}>{generating ? "生成中..." : "AI 生成标题和主题"}</button>
          </div>

          <div style={s.formSection}>
            <div style={s.formSectionTitle}>基本信息</div>
            <div style={s.formGroup}>
              <label style={s.formLabel}>标题</label>
              <input type="text" style={s.formInput} placeholder="小说标题" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
            </div>
            <div style={{ ...s.formGroup, ...s.formGroupLast }}>
              <label style={s.formLabel}>主题 / 核心设定</label>
              <textarea style={s.formTextarea} placeholder="一句话概括小说的核心世界观或主题" value={form.theme} onChange={(e) => setForm({ ...form, theme: e.target.value })} />
            </div>
          </div>

          <div style={s.formSection}>
            <div style={s.formSectionTitle}>类型</div>
            <div style={s.tagSelector}>
              {GENRE_OPTIONS.map((opt) => (
                <button key={opt} style={form.genre === opt ? s.tagOptionSelected : s.tagOption} onClick={() => setForm({ ...form, genre: opt })}>{opt}</button>
              ))}
            </div>
          </div>

          <div style={s.formSection}>
            <div style={s.formSectionTitle}>风格与视角</div>
            <TagGroup label="写作风格" options={STYLE_OPTIONS} value={form.style} onChange={(v) => setForm({ ...form, style: v })} />
            <div style={{ ...s.formGroup, ...s.formGroupLast }}>
              <TagGroup label="叙事视角" options={POV_OPTIONS} value={form.pov} onChange={(v) => setForm({ ...form, pov: v })} />
            </div>
          </div>

          <div style={s.formSection}>
            <div style={s.formSectionTitle}>创作参数</div>
            <Stepper label="目标章数" value={form.target_chapters} onChange={(v) => setForm({ ...form, target_chapters: v })} min={1} max={500} />
            <div style={{ ...s.formGroup, ...s.formGroupLast }}>
              <Stepper label="每章字数" value={form.words_per_chapter} onChange={(v) => setForm({ ...form, words_per_chapter: v })} min={500} max={50000} step={500} />
            </div>
          </div>

          <button style={s.submitBtn} onClick={handleSubmit} disabled={loading || !form.title}>{loading ? "创建中..." : "创建小说"}</button>
        </div>

        <PreviewCard config={form} />
      </div>
    </div>
  );
}
