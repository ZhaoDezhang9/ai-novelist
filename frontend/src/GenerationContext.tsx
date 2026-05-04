import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from "react";
import { api } from "./services/api";

interface GenerationState {
  storyId: string;
  chapterNumber: number;
  status: string; // "generating" | "checking" | "rewriting" | "saving" | "complete" | "idle" | "error"
  tokensReceived: number;
  contentChunks: string[];  // 保留完整内容，用于恢复
  contentPreview: string;
  errorMessage: string;
  updatedAt: string;
}

interface GenerationContextType {
  activeGenerations: Map<string, GenerationState>;
  getGeneration: (storyId: string) => GenerationState | undefined;
  isGenerating: (storyId: string) => boolean;
  /** 启动 SSE 生成 — 全局管理，切换页面不会断 */
  startGeneration: (storyId: string, chapterNumber: number) => void;
  /** 取消生成 */
  cancelGeneration: (storyId: string) => void;
  hasAnyActive: boolean;
}

const GenerationContext = createContext<GenerationContextType | null>(null);

export function GenerationProvider({ children }: { children: React.ReactNode }) {
  const [activeGenerations, setActiveGenerations] = useState<Map<string, GenerationState>>(new Map());
  const esRefs = useRef<Map<string, EventSource>>(new Map());
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // 启动时轮询后端，恢复可能正在进行的生成状态
  useEffect(() => {
    const pollActive = async () => {
      try {
        const active = await api.getActiveGenerations();
        if (active.length > 0) {
          setActiveGenerations((prev) => {
            const next = new Map(prev);
            for (const s of active) {
              if (!next.has(s.story_id) || next.get(s.story_id)!.status === "idle") {
                next.set(s.story_id, {
                  storyId: s.story_id,
                  chapterNumber: s.chapter_number,
                  status: s.status,
                  tokensReceived: s.tokens_received,
                  contentChunks: [],
                  contentPreview: "",
                  errorMessage: "",
                  updatedAt: s.updated_at,
                });
              }
            }
            return next;
          });
        }
      } catch {}
    };
    pollActive();
    pollRef.current = setInterval(pollActive, 10000);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, []);

  // 清理：组件卸载时关闭所有 EventSource
  useEffect(() => {
    return () => {
      esRefs.current.forEach((es) => es.close());
      esRefs.current.clear();
    };
  }, []);

  const getGeneration = useCallback((storyId: string) => activeGenerations.get(storyId), [activeGenerations]);

  const isGenerating = useCallback((storyId: string) => {
    const g = activeGenerations.get(storyId);
    return !!g && g.status !== "idle" && g.status !== "complete" && g.status !== "error";
  }, [activeGenerations]);

  const startGeneration = useCallback((storyId: string, chapterNumber: number) => {
    // 关闭已有的连接
    const existing = esRefs.current.get(storyId);
    if (existing) { existing.close(); esRefs.current.delete(storyId); }

    // 初始化状态
    setActiveGenerations((prev) => {
      const next = new Map(prev);
      next.set(storyId, {
        storyId, chapterNumber, status: "generating",
        tokensReceived: 0, contentChunks: [], contentPreview: "",
        errorMessage: "", updatedAt: new Date().toISOString(),
      });
      return next;
    });

    // 创建 SSE 连接
    const es = api.writeNextStream(storyId);
    esRefs.current.set(storyId, es);

    es.onmessage = (event) => {
      try {
        const evt = JSON.parse(event.data);
        setActiveGenerations((prev) => {
          const next = new Map(prev);
          const existing = next.get(storyId);
          if (!existing) return next;

          switch (evt.type) {
            case "token": {
              const newChunks = [...existing.contentChunks, evt.data];
              next.set(storyId, {
                ...existing,
                status: "generating",
                tokensReceived: existing.tokensReceived + 1,
                contentChunks: newChunks,
                contentPreview: newChunks.join("").slice(-200),
                updatedAt: new Date().toISOString(),
              });
              break;
            }
            case "check_complete":
              next.set(storyId, { ...existing, status: "checking", updatedAt: new Date().toISOString() });
              break;
            case "rewriting":
              next.set(storyId, { ...existing, status: "rewriting", updatedAt: new Date().toISOString() });
              break;
            case "chapter_complete":
              next.set(storyId, { ...existing, status: "complete", updatedAt: new Date().toISOString() });
              es.close();
              esRefs.current.delete(storyId);
              // 3秒后清除
              setTimeout(() => {
                setActiveGenerations((p) => { const n = new Map(p); n.delete(storyId); return n; });
              }, 3000);
              break;
            case "error":
              next.set(storyId, {
                ...existing, status: "error",
                errorMessage: evt.message || "生成失败",
                updatedAt: new Date().toISOString(),
              });
              es.close();
              esRefs.current.delete(storyId);
              break;
          }
          return next;
        });
      } catch {}
    };

    es.onerror = () => {
      setActiveGenerations((prev) => {
        const next = new Map(prev);
        const existing = next.get(storyId);
        if (existing && existing.status !== "complete" && existing.status !== "error") {
          next.set(storyId, {
            ...existing, status: "error",
            errorMessage: "连接中断",
            updatedAt: new Date().toISOString(),
          });
        }
        return next;
      });
      es.close();
      esRefs.current.delete(storyId);
    };
  }, []);

  const cancelGeneration = useCallback((storyId: string) => {
    const es = esRefs.current.get(storyId);
    if (es) { es.close(); esRefs.current.delete(storyId); }
    setActiveGenerations((prev) => {
      const next = new Map(prev);
      next.delete(storyId);
      return next;
    });
  }, []);

  const hasAnyActive = Array.from(activeGenerations.values()).some(
    (g) => g.status !== "idle" && g.status !== "complete" && g.status !== "error"
  );

  return (
    <GenerationContext.Provider value={{
      activeGenerations, getGeneration, isGenerating,
      startGeneration, cancelGeneration, hasAnyActive,
    }}>
      {children}
    </GenerationContext.Provider>
  );
}

export function useGeneration() {
  const ctx = useContext(GenerationContext);
  if (!ctx) throw new Error("useGeneration must be used within GenerationProvider");
  return ctx;
}
