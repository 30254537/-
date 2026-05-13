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
  intro_end?: number;
  first_drop?: number;
  breakdown?: number;
  outro_start?: number;
  beat_times?: string;
  downbeats?: string;
  waveform_bands?: string;
  hot_cues?: string;
  quality_verdict?: string;
  quality_score?: number;
  spectral_cutoff_hz?: number;
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

// ── Pro response shapes ───────────────────────────────────────────
export interface FingerprintMatch {
  track_id: number | null;
  title: string | null;
  artist: string | null;
  album: string | null;
  confidence: number;
  matched_landmarks: number;
  total_landmarks: number;
  source: string;
  metadata: Record<string, any>;
}

export interface TrackIdResult {
  local_matches: FingerprintMatch[];
  online: any | null;
  discogs: any | null;
}

export interface MixCandidate {
  track: Track;
  mix_score: number;
  bpm_delta: number;
  bpm_pct_change: number;
  harmonic: boolean;
  energy_delta: number;
  taste_similarity: number;
  reasons: string[];
  mix_in_at: number | null;
  mix_out_at: number | null;
}

export interface PhraseBoundary {
  time_sec: number;
  bar: number;
  type: "8" | "16" | "32";
  label?: string | null;
}

export interface PhraseSection {
  start_sec: number;
  end_sec: number;
  bar_start: number;
  bar_end: number;
  energy_density: number;
  label: string;
}

export interface PhraseGrid {
  track_id: number;
  bpm: number | null;
  bars_per_phrase: number;
  total_bars: number;
  boundaries: PhraseBoundary[];
  sections: PhraseSection[];
  mix_in_points: number[];
  mix_out_points: number[];
}

export interface HotCue {
  slot: number;
  name: string;
  time_sec: number;
  color: string;
  type: string;
}

export interface QualityReport {
  path: string;
  declared_bitrate_kbps: number | null;
  container: string;
  sample_rate: number;
  measured_cutoff_hz: number;
  verdict: string;
  score: number;
  notes: string[];
  spectrum_db: number[];
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

  train: () => req<any>("/api/ai/train", { method: "POST" }),

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

  // ── Pro modules ──────────────────────────────────────────────────
  pro: {
    trackIdFile: (path: string) =>
      req<TrackIdResult>("/api/pro/trackid/file", {
        method: "POST",
        body: JSON.stringify({ path }),
      }),
    trackIdLibrary: (id: number) =>
      req<TrackIdResult>(`/api/pro/trackid/library/${id}`, { method: "POST" }),

    liveMixSuggest: (current_track_id: number, mode = "steady", limit = 3) =>
      req<{ candidates: MixCandidate[] }>("/api/pro/livemix/suggest", {
        method: "POST",
        body: JSON.stringify({ current_track_id, mode, limit }),
      }),
    liveMixPlayed: (id: number) =>
      req<{ ok: true }>(`/api/pro/livemix/played/${id}`, { method: "POST" }),

    phraseGrid: (id: number, bars = 32) =>
      req<PhraseGrid>(`/api/pro/phrasegrid/${id}?bars_per_phrase=${bars}`),

    stemsCapabilities: () =>
      req<{ available: boolean; backend: string | null; stems: string[]; install_hint: string | null }>(
        "/api/pro/stems/capabilities"
      ),
    stemsSeparate: (track_id: number, out_dir?: string) =>
      req<{ stems: Record<string, string>; backend: string; out_dir: string }>(
        "/api/pro/stems/separate",
        {
          method: "POST",
          body: JSON.stringify({ track_id, out_dir }),
        }
      ),

    gigExport: (params: {
      out_root: string;
      playlist_id?: number;
      track_ids?: number[];
      playlist_name?: string;
      normalize_lufs?: number | null;
      include_covers?: boolean;
    }) =>
      req<{ out_dir: string; track_count: number; total_size_mb: number; failures: string[] }>(
        "/api/pro/gig/export",
        { method: "POST", body: JSON.stringify(params) }
      ),

    trends: (genres?: string, refresh = false) => {
      const qs = new URLSearchParams();
      if (genres) qs.set("genres", genres);
      if (refresh) qs.set("refresh", "true");
      return req<{ sections: any[]; online: boolean }>(`/api/pro/trends?${qs.toString()}`);
    },

    qualityTrack: (id: number) =>
      req<QualityReport>(`/api/pro/quality/${id}`),
    qualityBatch: (track_ids?: number[], limit = 200) =>
      req<{ reports: any[]; count: number }>("/api/pro/quality/audit", {
        method: "POST",
        body: JSON.stringify({ track_ids, limit }),
      }),

    hotCuesGenerate: (id: number, save = true) =>
      req<{ track_id: number; duration: number; bpm: number; cues: HotCue[] }>(
        `/api/pro/hotcues/${id}?save=${save}`,
        { method: "POST" }
      ),
    hotCuesGet: (id: number) =>
      req<{ track_id: number; cues: HotCue[] }>(`/api/pro/hotcues/${id}`),
  },
};
