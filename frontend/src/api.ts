// API client for MixMind DJ backend

export interface Track {
  id: number;
  path: string;
  filename: string;
  title?: string;
  artist?: string;
  album?: string;
  duration?: number;
  bpm?: number;
  key_name?: string;
  camelot?: string;
  energy?: number;
  loudness?: number;
  brightness?: number;
  danceability?: number;
  genre_ai?: string;
  genre_tag?: string;
  mood_label?: string;
  rating?: number;
  peak_start?: number;
  peak_end?: number;
  duplicate_group_id?: number;
  similarity_score?: number;
}

export interface Stats {
  total_tracks: number;
  analyzed: number;
  liked: number;
  disliked: number;
  duplicates: number;
  total_hours: number;
  genres: Array<{ genre_ai: string; c: number }>;
  moods: Array<{ mood_label: string; c: number }>;
}

const API_BASE = "";

async function req<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(API_BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json();
}

export const api = {
  health: () => req<{ ok: boolean; version: string }>("/api/health"),
  stats: () => req<Stats>("/api/stats"),

  listTracks: (params: Record<string, any> = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== "")
    ).toString();
    return req<{ tracks: Track[]; count: number }>(`/api/tracks?${qs}`);
  },

  getTrack: (id: number) => req<Track>(`/api/tracks/${id}`),

  rateTrack: (id: number, rating: number) =>
    req<{ ok: boolean }>(`/api/tracks/${id}/rate`, {
      method: "POST",
      body: JSON.stringify({ rating }),
    }),

  similar: (id: number, limit = 20) =>
    req<{ tracks: Track[] }>(`/api/tracks/${id}/similar?limit=${limit}`),

  recommend: (limit = 20) =>
    req<{ tracks: Track[] }>(`/api/ai/recommend?limit=${limit}`),

  train: () =>
    req<any>("/api/ai/train", { method: "POST" }),

  startScan: (folder: string, analyze = true) =>
    req<{ job_id: string }>("/api/scan", {
      method: "POST",
      body: JSON.stringify({ folder, analyze }),
    }),

  jobStatus: (id: string) =>
    req<{ status: string; total: number; done: number; error?: string }>(`/api/jobs/${id}`),

  dedupe: () =>
    req<{ groups: number; tracks: number; data: Track[][] }>("/api/dedupe", {
      method: "POST",
    }),

  generatePlaylist: (params: {
    duration_minutes: number;
    curve: string;
    genre?: string;
    bpm_min?: number;
    bpm_max?: number;
    save_as?: string;
  }) =>
    req<{ tracks: Track[]; playlist_id: number | null }>("/api/playlist/generate", {
      method: "POST",
      body: JSON.stringify(params),
    }),

  audioUrl: (id: number) => `/api/tracks/${id}/audio`,

  genres: () => req<{ genres: string[] }>("/api/genres"),
  moods: () => req<{ moods: string[] }>("/api/moods"),
};
