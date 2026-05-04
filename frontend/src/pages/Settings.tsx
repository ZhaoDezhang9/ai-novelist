import React, { useState, useEffect, useCallback } from "react";
import { colors, space, fonts, input, radius } from "../styles";
import { api, AppSettings } from "../services/api";

const LS_KEY = "ai-novelist-settings";

const DEFAULTS: AppSettings = {
  llm_api_key: "",
  llm_api_base: "https://api.deepseek.com/v1",
  llm_model: "deepseek-v4-pro",
  llm_fast_model: "deepseek-v4-flash",
  llm_temperature: 0.85,
  llm_top_p: 0.92,
  llm_max_tokens: 8192,
  max_rewrite_rounds: 3,
  alignment_score_min: 0.75,
  ngram_overlap_threshold: 0.15,
  template_similarity_threshold: 0.7,
  vocab_diversity_threshold: 0.4,
  twist_density_min: 0.00033,
  rewrite_window_lines: 400,
  hot_chapters: 2,
  warm_summary_chapters: 5,
  max_context_tokens: 64000,
};

function loadLocal(): AppSettings {
  try {
    const raw = localStorage.getItem(LS_KEY);
    if (raw) return { ...DEFAULTS, ...JSON.parse(raw) };
  } catch {}
  return { ...DEFAULTS };
}

function saveLocal(settings: AppSettings) {
  localStorage.setItem(LS_KEY, JSON.stringify(settings));
}

type ToastType = "success" | "local";

export default function Settings() {
  const [form, setForm] = useState<AppSettings>(loadLocal);
  const [showKey, setShowKey] = useState(false);
  const [toast, setToast] = useState<{ type: ToastType; msg: string } | null>(null);
  const [apiUnavailable, setApiUnavailable] = useState(false);

  useEffect(() => {
    api.getSettings().then((s) => {
      setForm(s);
      saveLocal(s);
      setApiUnavailable(false);
    }).catch(() => {
      setForm(loadLocal());
      setApiUnavailable(true);
    });
  }, []);

  const showToast = useCallback((type: ToastType, msg: string) => {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 2000);
  }, []);

  const patch = (key: keyof AppSettings, value: string | number) => {
    setForm((f) => ({ ...f, [key]: value }));
  };

  const handleSave = async () => {
    saveLocal(form);
    try {
      await api.updateSettings(form);
      setApiUnavailable(false);
      showToast("success", "设置已保存");
    } catch {
      setApiUnavailable(true);
      showToast("local", "设置已保存到本地");
    }
  };

  const sectionCardStyle: React.CSSProperties = {
    background: colors.surfaceRaised,
    border: `1px solid ${colors.border}`,
    borderRadius: radius.md,
    padding: "28px",
    marginBottom: "20px",
  };

  const sectionTitleStyle: React.CSSProperties = {
    fontFamily: fonts.display,
    fontSize: "17px",
    fontWeight: 600,
    marginBottom: "20px",
    paddingBottom: "12px",
    borderBottom: `1px solid ${colors.borderLight}`,
  };

  const rowStyle: React.CSSProperties = {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "12px 0",
    borderBottom: `1px solid ${colors.borderLight}`,
  };

  const labelStyle: React.CSSProperties = {
    fontSize: "14px",
    color: colors.fgSecondary,
  };

  const inputStyle: React.CSSProperties = {
    width: "240px",
    textAlign: "right",
    padding: `${space[2]} ${space[3]}`,
    fontSize: "14px",
    fontFamily: "inherit",
    background: colors.surface,
    border: `1px solid ${colors.border}`,
    borderRadius: radius.sm,
    color: colors.fg,
    outline: "none",
  };

  const numberInputStyle: React.CSSProperties = {
    ...inputStyle,
    width: "240px",
  };

  const eyeBtnStyle: React.CSSProperties = {
    position: "absolute",
    right: space[2],
    top: "50%",
    transform: "translateY(-50%)",
    background: "none",
    border: "none",
    cursor: "pointer",
    color: colors.muted,
    padding: space[1],
    display: "flex",
    alignItems: "center",
  };

  return (
    <div style={{ maxWidth: "680px", margin: "0 auto", padding: space[6] }}>
      <h1 style={{ fontFamily: fonts.display, fontSize: "22px", fontWeight: 700, color: colors.fg, marginBottom: "24px" }}>设置</h1>

      {/* Toast */}
      {toast && (
        <div style={{
          position: "fixed",
          top: space[4],
          left: "50%",
          transform: "translateX(-50%)",
          zIndex: 1000,
          background: toast.type === "success" ? colors.primary : colors.surfaceRaised,
          color: toast.type === "success" ? "#fff" : colors.fg,
          border: `1px solid ${toast.type === "success" ? colors.primaryBorder : colors.border}`,
          borderRadius: "8px",
          padding: `${space[3]} ${space[5]}`,
          fontSize: "13px",
          fontWeight: 600,
          boxShadow: "0 4px 24px rgba(0,0,0,0.4)",
        }}>
          {toast.msg}
        </div>
      )}

      {apiUnavailable && (
        <div style={{
          background: colors.infoMuted,
          border: `1px solid ${colors.infoBorder}`,
          borderRadius: "8px",
          padding: `${space[3]} ${space[4]}`,
          marginBottom: space[5],
          fontSize: "13px",
          color: colors.info,
        }}>
          后端 API 不可用，设置将保存到本地
        </div>
      )}

      {/* Section 1: AI 模型配置 */}
      <div style={sectionCardStyle}>
        <div style={sectionTitleStyle}>AI 模型配置</div>

        <div style={rowStyle}>
          <label style={labelStyle}>API 地址</label>
          <input
            type="text"
            value={form.llm_api_base}
            onChange={(e) => patch("llm_api_base", e.target.value)}
            style={inputStyle}
          />
        </div>

        <div style={{ ...rowStyle, position: "relative" }}>
          <label style={labelStyle}>API Key</label>
          <div style={{ position: "relative" }}>
            <input
              type={showKey ? "text" : "password"}
              value={form.llm_api_key}
              onChange={(e) => patch("llm_api_key", e.target.value)}
              placeholder="sk-..."
              style={{ ...inputStyle, paddingRight: "36px" }}
            />
            <button type="button" style={eyeBtnStyle} onClick={() => setShowKey((v) => !v)}>
              {showKey ? (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                  <line x1="1" y1="1" x2="23" y2="23"/>
                </svg>
              ) : (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                  <circle cx="12" cy="12" r="3"/>
                </svg>
              )}
            </button>
          </div>
        </div>

        <div style={rowStyle}>
          <label style={labelStyle}>主模型</label>
          <input
            type="text"
            value={form.llm_model}
            onChange={(e) => patch("llm_model", e.target.value)}
            style={inputStyle}
          />
        </div>

        <div style={{ ...rowStyle, borderBottom: "none" }}>
          <label style={labelStyle}>轻量模型</label>
          <input
            type="text"
            value={form.llm_fast_model}
            onChange={(e) => patch("llm_fast_model", e.target.value)}
            style={inputStyle}
          />
        </div>
      </div>

      {/* Section 2: 生成参数 */}
      <div style={sectionCardStyle}>
        <div style={sectionTitleStyle}>生成参数</div>

        <div style={rowStyle}>
          <label style={labelStyle}>Temperature</label>
          <input
            type="number"
            step="0.01"
            value={form.llm_temperature}
            onChange={(e) => patch("llm_temperature", parseFloat(e.target.value) || 0)}
            style={numberInputStyle}
          />
        </div>

        <div style={rowStyle}>
          <label style={labelStyle}>Max Tokens</label>
          <input
            type="number"
            value={form.llm_max_tokens}
            onChange={(e) => patch("llm_max_tokens", parseInt(e.target.value) || 0)}
            style={numberInputStyle}
          />
        </div>

        <div style={{ ...rowStyle, borderBottom: "none" }}>
          <label style={labelStyle}>最大改写轮数</label>
          <input
            type="number"
            value={form.max_rewrite_rounds}
            onChange={(e) => patch("max_rewrite_rounds", parseInt(e.target.value) || 1)}
            style={numberInputStyle}
          />
        </div>
      </div>

      {/* Section 3: 质量阈值 */}
      <div style={sectionCardStyle}>
        <div style={sectionTitleStyle}>质量阈值</div>

        <div style={rowStyle}>
          <label style={labelStyle}>一致性检查 (L1/L2/L3)</label>
          <input
            type="number"
            step="0.01"
            value={form.ngram_overlap_threshold}
            onChange={(e) => patch("ngram_overlap_threshold", parseFloat(e.target.value) || 0)}
            style={numberInputStyle}
          />
        </div>

        <div style={rowStyle}>
          <label style={labelStyle}>原创性阈值</label>
          <input
            type="number"
            step="0.01"
            value={form.template_similarity_threshold}
            onChange={(e) => patch("template_similarity_threshold", parseFloat(e.target.value) || 0)}
            style={numberInputStyle}
          />
        </div>

        <div style={{ ...rowStyle, borderBottom: "none" }}>
          <label style={labelStyle}>大纲对齐阈值</label>
          <input
            type="number"
            step="0.01"
            value={form.alignment_score_min}
            onChange={(e) => patch("alignment_score_min", parseFloat(e.target.value) || 0)}
            style={numberInputStyle}
          />
        </div>
      </div>

      {/* Section 4: 记忆系统 */}
      <div style={sectionCardStyle}>
        <div style={sectionTitleStyle}>记忆系统</div>

        <div style={rowStyle}>
          <label style={labelStyle}>热记忆 (最近 N 章)</label>
          <input
            type="number"
            value={form.hot_chapters}
            onChange={(e) => patch("hot_chapters", parseInt(e.target.value) || 1)}
            style={numberInputStyle}
          />
        </div>

        <div style={{ ...rowStyle, borderBottom: "none" }}>
          <label style={labelStyle}>温记忆摘要长度</label>
          <input
            type="number"
            value={form.warm_summary_chapters}
            onChange={(e) => patch("warm_summary_chapters", parseInt(e.target.value) || 1)}
            style={numberInputStyle}
          />
        </div>
      </div>

      {/* Save Button */}
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <button
          type="button"
          onClick={handleSave}
          style={{
            padding: "12px 32px",
            background: colors.accent,
            color: "#fff",
            border: "none",
            borderRadius: "6px",
            fontSize: "14px",
            fontWeight: 500,
            cursor: "pointer",
          }}
        >
          保存设置
        </button>
      </div>
    </div>
  );
}