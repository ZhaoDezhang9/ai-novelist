const BASE = "/api";

// ========== Types ==========

export interface StoryConfig {
  title: string;
  genre: string;
  style: string;
  pov: string;
  target_chapters: number;
  words_per_chapter: number;
  target_audience: string;
  theme: string;
}

export interface StoryListItem {
  id: string;
  title: string;
  genre: string;
  style: string;
  current_chapter: number;
  target_chapters: number;
  status: string;
  created_at: string;
}

export interface ChapterInfo {
  chapter_number: number;
  title: string;
  word_count: number;
  status: string;
  alignment_score: number;
  originality_score: number;
  rewrites_count: number;
}

export interface ChapterDetail extends ChapterInfo {
  content: string;
  check_results: Array<{
    layer: string;
    passed: boolean;
    issues_count: number;
    issues: Array<{
      type: string;
      severity: string;
      description: string;
      suggestion?: string;
      location?: string;
    }>;
    scores: Record<string, number>;
  }>;
  emotion_curve: Array<{
    position_pct: number;
    tension: number;
    relaxation: number;
    sadness: number;
    pleasure: number;
  }>;
}

export interface StyleVector {
  avg_sentence_length: number;
  dialogue_ratio: number;
  metaphor_density: number;
  adverb_ratio: number;
  paragraph_length_median: number;
  perspective_consistency: number;
}

export interface OutlineNode {
  chapter: number;
  title: string;
  goal: string;
  plot_points: string[];
  emotional_beat: string;
  key_characters: string[];
  foreshadowing_seeds: string[];
  twist_note: string;
  act?: string;
}

export interface WorldBible {
  setting: string;
  rules: string[];
  factions: string[];
  timeline: Record<string, string>;
}

export interface Character {
  name: string;
  role: string;
  arc: string;
  traits?: string;
  gender?: string;
  age?: string;
  personality?: string;
  background?: string;
  motivation?: string;
  relationships?: string[];
  secrets?: string;
  status?: string;
  weakness?: string;
  voice?: string;
}

export interface Foreshadowing {
  id: string;
  planted_chapter: number;
  description: string;
  payoff_chapter?: number | null;
  status: string;
  min_payoff_chapter?: number | null;
}

export interface StoryDetail {
  id: string;
  config: StoryConfig & { style_vector?: StyleVector };
  outline: OutlineNode[];
  world_bible: WorldBible;
  characters: Character[];
  foreshadowing_list: Foreshadowing[];
  current_chapter: number;
}

export interface CreateStoryResponse {
  id: string;
  title: string;
  genre: string;
  style: string;
  total_chapters: number;
  world_bible: WorldBible;
  characters_count: number;
}

export interface WriteNextResponse {
  chapter_number: number;
  title: string;
  content: string;
  word_count: number;
  status: string;
  check_results: Array<{
    layer: string;
    passed: boolean;
    issues_count: number;
    issues: Array<{
      type: string;
      severity: string;
      description: string;
      suggestion?: string;
    }>;
    scores: Record<string, number>;
  }>;
  rewrites_count: number;
}

export interface RewriteResponse {
  chapter_number: number;
  content: string;
  word_count: number;
  issues_found: number;
  rewrites_count: number;
}

export interface AppSettings {
  llm_api_key: string;
  llm_api_base: string;
  llm_model: string;
  llm_fast_model: string;
  llm_temperature: number;
  llm_top_p: number;
  llm_max_tokens: number;
  max_rewrite_rounds: number;
  alignment_score_min: number;
  ngram_overlap_threshold: number;
  template_similarity_threshold: number;
  vocab_diversity_threshold: number;
  twist_density_min: number;
  rewrite_window_lines: number;
  hot_chapters: number;
  warm_summary_chapters: number;
  max_context_tokens: number;
}

// ========== SSE Stream Event ==========

export interface StreamEvent {
  type: "token" | "check_complete" | "rewriting" | "chapter_complete" | "error";
  data?: string;
  message?: string;
  chapter_number?: number;
  word_count?: number;
  round?: number;
  issues_count?: number;
  results?: Array<{ layer: string; passed: boolean }>;
}

// ========== Fetch Helper ==========

interface FetchOptions extends RequestInit {
  retries?: number;
  retryDelay?: number;
  timeout?: number;
}

async function apiFetch<T>(url: string, init?: FetchOptions): Promise<T> {
  const { retries = 0, retryDelay = 1000, timeout = 30000, ...fetchInit } = init || {};
  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      if (attempt > 0) {
        await new Promise((r) => setTimeout(r, retryDelay * Math.pow(2, attempt - 1)));
      }
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), timeout);
      const res = await fetch(url, { ...fetchInit, signal: controller.signal });
      clearTimeout(timer);
      if (!res.ok) {
        const detail = await res.text().catch(() => res.statusText);
        const err = new Error(detail || `请求失败 (${res.status})`);
        if (res.status >= 500 && attempt < retries) { lastError = err; continue; }
        throw err;
      }
      return res.json();
    } catch (e) {
      if (e instanceof DOMException && e.name === "AbortError") {
        throw new Error("请求超时，请检查网络或后端服务");
      }
      lastError = e instanceof Error ? e : new Error("请求失败");
      if (attempt >= retries) throw lastError;
    }
  }
  throw lastError || new Error("请求失败");
}

// ========== API ==========

export interface ApiCallOptions {
  signal?: AbortSignal;
}

export const api = {
  createStory: async (config: StoryConfig, opts?: ApiCallOptions): Promise<CreateStoryResponse> =>
    apiFetch<CreateStoryResponse>(`${BASE}/stories`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
      signal: opts?.signal,
      timeout: 120000,  // 创建涉及多次LLM调用，需要较长时间
    }),

  generateMeta: async (idea: string, genre: string, opts?: ApiCallOptions): Promise<{ title: string; theme: string }> =>
    apiFetch<{ title: string; theme: string }>(`${BASE}/stories/generate-meta`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ idea, genre }),
      signal: opts?.signal,
    }),

  listStories: async (opts?: ApiCallOptions): Promise<StoryListItem[]> =>
    apiFetch<StoryListItem[]>(`${BASE}/stories`, { signal: opts?.signal, retries: 2 }),

  getStory: async (id: string, opts?: ApiCallOptions): Promise<StoryDetail> =>
    apiFetch<StoryDetail>(`${BASE}/stories/${id}`, { signal: opts?.signal, retries: 2 }),

  deleteStory: async (id: string): Promise<void> => {
    const res = await fetch(`${BASE}/stories/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error("删除失败");
  },

  listChapters: async (storyId: string, opts?: ApiCallOptions): Promise<ChapterInfo[]> =>
    apiFetch<ChapterInfo[]>(`${BASE}/chapters/${storyId}/list`, { signal: opts?.signal, retries: 2 }),

  getChapter: async (storyId: string, num: number, opts?: ApiCallOptions): Promise<ChapterDetail> =>
    apiFetch<ChapterDetail>(`${BASE}/chapters/${storyId}/chapter/${num}`, { signal: opts?.signal, retries: 2 }),

  writeNext: async (storyId: string, opts?: ApiCallOptions): Promise<WriteNextResponse> =>
    apiFetch<WriteNextResponse>(`${BASE}/chapters/${storyId}/write-next`, { method: "POST", signal: opts?.signal }),

  writeNextStream: (storyId: string): EventSource =>
    new EventSource(`${BASE}/chapters/${storyId}/write-next-stream`),

  writeAll: async (storyId: string, from?: number, opts?: ApiCallOptions): Promise<{ chapters_written: number; chapters: ChapterInfo[] }> => {
    const url = `${BASE}/chapters/${storyId}/write-all${from ? `?start_from=${from}` : ""}`;
    return apiFetch(url, { method: "POST", signal: opts?.signal });
  },

  rewriteChapter: async (storyId: string, chapterNumber: number, opts?: ApiCallOptions): Promise<RewriteResponse> =>
    apiFetch<RewriteResponse>(`${BASE}/chapters/${storyId}/chapter/${chapterNumber}/rewrite`, { method: "POST", signal: opts?.signal }),

  getGenerationStatus: async (storyId: string, opts?: ApiCallOptions): Promise<{
    story_id: string; chapter_number: number; status: string;
    tokens_received: number; content_preview: string; updated_at: string;
  }> => apiFetch(`${BASE}/chapters/${storyId}/generation-status`, { signal: opts?.signal }),

  getActiveGenerations: async (opts?: ApiCallOptions): Promise<Array<{
    story_id: string; chapter_number: number; status: string;
    tokens_received: number; updated_at: string;
  }>> => apiFetch(`${BASE}/chapters/generation-active`, { signal: opts?.signal }),

  getSettings: async (opts?: ApiCallOptions): Promise<AppSettings> =>
    apiFetch<AppSettings>(`${BASE}/settings`, { signal: opts?.signal, retries: 2 }),

  updateSettings: async (settings: Partial<AppSettings>, opts?: ApiCallOptions): Promise<AppSettings> =>
    apiFetch<AppSettings>(`${BASE}/settings`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings),
      signal: opts?.signal,
    }),
};
