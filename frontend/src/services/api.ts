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

async function apiFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(detail || `请求失败 (${res.status})`);
  }
  return res.json();
}

// ========== API ==========

export const api = {
  // Stories
  createStory: async (config: StoryConfig): Promise<CreateStoryResponse> =>
    apiFetch<CreateStoryResponse>(`${BASE}/stories`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    }),

  generateMeta: async (idea: string, genre: string): Promise<{ title: string; theme: string }> =>
    apiFetch<{ title: string; theme: string }>(`${BASE}/stories/generate-meta`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ idea, genre }),
    }),

  listStories: async (): Promise<StoryListItem[]> =>
    apiFetch<StoryListItem[]>(`${BASE}/stories`),

  getStory: async (id: string): Promise<StoryDetail> =>
    apiFetch<StoryDetail>(`${BASE}/stories/${id}`),

  deleteStory: async (id: string): Promise<void> => {
    const res = await fetch(`${BASE}/stories/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error("删除失败");
  },

  // Chapters
  listChapters: async (storyId: string): Promise<ChapterInfo[]> =>
    apiFetch<ChapterInfo[]>(`${BASE}/chapters/${storyId}/list`),

  getChapter: async (storyId: string, num: number): Promise<ChapterDetail> =>
    apiFetch<ChapterDetail>(`${BASE}/chapters/${storyId}/chapter/${num}`),

  writeNext: async (storyId: string): Promise<WriteNextResponse> =>
    apiFetch<WriteNextResponse>(`${BASE}/chapters/${storyId}/write-next`, { method: "POST" }),

  writeNextStream: (storyId: string): EventSource =>
    new EventSource(`${BASE}/chapters/${storyId}/write-next-stream`),

  writeAll: async (storyId: string, from?: number): Promise<{ chapters_written: number; chapters: ChapterInfo[] }> => {
    const url = `${BASE}/chapters/${storyId}/write-all${from ? `?start_from=${from}` : ""}`;
    return apiFetch(url, { method: "POST" });
  },

  rewriteChapter: async (storyId: string, chapterNumber: number): Promise<RewriteResponse> =>
    apiFetch<RewriteResponse>(`${BASE}/chapters/${storyId}/chapter/${chapterNumber}/rewrite`, { method: "POST" }),

  // Generation Status
  getGenerationStatus: async (storyId: string): Promise<{
    story_id: string; chapter_number: number; status: string;
    tokens_received: number; content_preview: string; updated_at: string;
  }> => apiFetch(`${BASE}/chapters/${storyId}/generation-status`),

  getActiveGenerations: async (): Promise<Array<{
    story_id: string; chapter_number: number; status: string;
    tokens_received: number; updated_at: string;
  }>> => apiFetch(`${BASE}/chapters/generation-active`),

  // Settings
  getSettings: async (): Promise<AppSettings> =>
    apiFetch<AppSettings>(`${BASE}/settings`),

  updateSettings: async (settings: Partial<AppSettings>): Promise<AppSettings> =>
    apiFetch<AppSettings>(`${BASE}/settings`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings),
    }),
};
