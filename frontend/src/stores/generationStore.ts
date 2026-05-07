import { create } from "zustand";
import { api } from "../services/api";

interface GenerationState {
  storyId: string;
  chapterNumber: number;
  status: string;
  tokensReceived: number;
  contentChunks: string[];
  contentPreview: string;
  errorMessage: string;
  updatedAt: string;
}

interface GenerationStore {
  activeGenerations: Map<string, GenerationState>;
  getGeneration: (storyId: string) => GenerationState | undefined;
  isGenerating: (storyId: string) => boolean;
  startGeneration: (storyId: string, chapterNumber: number) => void;
  cancelGeneration: (storyId: string) => void;
  hasAnyActive: () => boolean;
}

const esRefs = new Map<string, EventSource>();
const abortRefs = new Map<string, AbortController>();

let pollTimer: ReturnType<typeof setInterval> | null = null;

function startPolling() {
  if (pollTimer) return;
  const poll = async () => {
    try {
      const active = await api.getActiveGenerations();
      if (active.length > 0) {
        useGenerationStore.setState((s) => {
          const next = new Map(s.activeGenerations);
          for (const st of active) {
            if (!next.has(st.story_id) || next.get(st.story_id)!.status === "idle") {
              next.set(st.story_id, {
                storyId: st.story_id, chapterNumber: st.chapter_number,
                status: st.status, tokensReceived: st.tokens_received,
                contentChunks: [], contentPreview: "", errorMessage: "",
                updatedAt: st.updated_at,
              });
            }
          }
          return { activeGenerations: next };
        });
      }
    } catch {}
  };
  poll();
  pollTimer = setInterval(poll, 10000);
}

startPolling();

export const useGenerationStore = create<GenerationStore>((set, get) => ({
  activeGenerations: new Map(),

  getGeneration: (storyId) => get().activeGenerations.get(storyId),

  isGenerating: (storyId) => {
    const g = get().activeGenerations.get(storyId);
    return !!g && g.status !== "idle" && g.status !== "complete" && g.status !== "error";
  },

  startGeneration: (storyId, chapterNumber) => {
    // Clean up existing connections
    const existingEs = esRefs.get(storyId);
    if (existingEs) { existingEs.close(); esRefs.delete(storyId); }
    const existingAbort = abortRefs.get(storyId);
    if (existingAbort) { existingAbort.abort(); abortRefs.delete(storyId); }

    const abortController = new AbortController();
    abortRefs.set(storyId, abortController);

    set((s) => {
      const next = new Map(s.activeGenerations);
      next.set(storyId, {
        storyId, chapterNumber, status: "generating",
        tokensReceived: 0, contentChunks: [], contentPreview: "",
        errorMessage: "", updatedAt: new Date().toISOString(),
      });
      return { activeGenerations: next };
    });

    const es = api.writeNextStream(storyId);
    esRefs.set(storyId, es);

    es.onmessage = (event) => {
      try {
        const evt = JSON.parse(event.data);
        set((s) => {
          const next = new Map(s.activeGenerations);
          const existing = next.get(storyId);
          if (!existing) return { activeGenerations: next };

          switch (evt.type) {
            case "token": {
              const newChunks = [...existing.contentChunks, evt.data];
              next.set(storyId, {
                ...existing, status: "generating",
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
              es.close(); esRefs.delete(storyId); abortRefs.delete(storyId);
              setTimeout(() => {
                set((p) => { const n = new Map(p.activeGenerations); n.delete(storyId); return { activeGenerations: n }; });
              }, 3000);
              break;
            case "error":
              next.set(storyId, {
                ...existing, status: "error",
                errorMessage: evt.message || "生成失败",
                updatedAt: new Date().toISOString(),
              });
              es.close(); esRefs.delete(storyId); abortRefs.delete(storyId);
              break;
          }
          return { activeGenerations: next };
        });
      } catch {}
    };

    es.onerror = () => {
      set((s) => {
        const next = new Map(s.activeGenerations);
        const existing = next.get(storyId);
        if (existing && existing.status !== "complete" && existing.status !== "error") {
          next.set(storyId, { ...existing, status: "error", errorMessage: "连接中断", updatedAt: new Date().toISOString() });
        }
        return { activeGenerations: next };
      });
      es.close(); esRefs.delete(storyId); abortRefs.delete(storyId);
    };
  },

  cancelGeneration: (storyId) => {
    const es = esRefs.get(storyId);
    if (es) { es.close(); esRefs.delete(storyId); }
    const abort = abortRefs.get(storyId);
    if (abort) { abort.abort(); abortRefs.delete(storyId); }
    set((s) => {
      const next = new Map(s.activeGenerations);
      next.delete(storyId);
      return { activeGenerations: next };
    });
  },

  hasAnyActive: () => {
    return Array.from(get().activeGenerations.values()).some(
      (g) => g.status !== "idle" && g.status !== "complete" && g.status !== "error"
    );
  },
}));
