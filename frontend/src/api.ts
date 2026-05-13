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

  // ── Pro Plus (v0.5) ─────────────────────────────────────────────
  pp: {
    autotagPlan: (out_root: string, track_ids?: number[]) =>
      req<{ plan: any[] }>("/api/pro/autotag/plan", {
        method: "POST",
        body: JSON.stringify({ out_root, track_ids }),
      }),
    autotagExecute: (
      out_root: string,
      mode = "copy",
      track_ids?: number[],
      update_paths = false,
    ) =>
      req<any>("/api/pro/autotag/execute", {
        method: "POST",
        body: JSON.stringify({ out_root, mode, track_ids, update_paths }),
      }),

    coverRun: (online = true, track_ids?: number[]) =>
      req<{ extracted: number; fetched: number; failed: number }>(
        "/api/pro/coverart/run",
        { method: "POST", body: JSON.stringify({ online, track_ids }) }
      ),
    coverUrl: (id: number) => `/api/pro/coverart/${id}`,

    vibeTag: (track_ids?: number[]) =>
      req<any>("/api/pro/vibe/tag", { method: "POST", body: JSON.stringify({ track_ids }) }),
    vibeFind: (params: Record<string, any>) => {
      const qs = new URLSearchParams(
        Object.entries(params).filter(([, v]) => v != null && v !== "")
      ).toString();
      return req<{ tracks: Track[] }>(`/api/pro/vibe/find?${qs}`);
    },

    sonicSimilarity: (id: number, opts: Record<string, any> = {}) => {
      const qs = new URLSearchParams(
        Object.entries(opts).filter(([, v]) => v != null && v !== "")
      ).toString();
      return req<{ tracks: any[] }>(`/api/pro/similarity/${id}?${qs}`);
    },

    tracklistRecover: (set_path: string, opts: Record<string, any> = {}) =>
      req<any>("/api/pro/tracklist/recover", {
        method: "POST",
        body: JSON.stringify({ set_path, ...opts }),
      }),
    tracklistFormat: (tracklist: any, format: string = "text") =>
      req<{ text: string }>("/api/pro/tracklist/format", {
        method: "POST",
        body: JSON.stringify({ tracklist, format }),
      }),

    historyList: () => req<any>("/api/pro/sethistory"),
    historyRecord: (name: string, tracklist: any, venue?: string, notes?: string) =>
      req<any>("/api/pro/sethistory/record", {
        method: "POST",
        body: JSON.stringify({ name, tracklist, venue, notes }),
      }),
    historyProfile: (since_days?: number) =>
      req<any>(`/api/pro/sethistory/profile${since_days ? `?since_days=${since_days}` : ""}`),
    historyDrift: () => req<any>("/api/pro/sethistory/drift"),

    mimicFingerprint: (tracks: any[]) =>
      req<any>("/api/pro/mimic/fingerprint", {
        method: "POST",
        body: JSON.stringify({ tracks }),
      }),
    mimicGenerate: (fingerprint: any, target_count?: number) =>
      req<{ tracks: Track[] }>("/api/pro/mimic/generate", {
        method: "POST",
        body: JSON.stringify({ fingerprint, target_count }),
      }),

    b2bCompare: (your_ids: number[], partner_meta: any[]) =>
      req<any>("/api/pro/b2b/compare", {
        method: "POST",
        body: JSON.stringify({ your_ids, partner_meta }),
      }),
    b2bSetlist: (your_ids: number[], partner_meta: any[], duration_minutes = 60) =>
      req<{ tracks: any[] }>("/api/pro/b2b/setlist", {
        method: "POST",
        body: JSON.stringify({ your_ids, partner_meta, duration_minutes }),
      }),

    highlightFind: (set_path: string, clip_seconds = 30, n_top = 1) =>
      req<any>("/api/pro/highlight/find", {
        method: "POST",
        body: JSON.stringify({ set_path, clip_seconds, n_top }),
      }),
    highlightExport: (set_path: string, out_path: string, start_sec: number, duration_sec = 30) =>
      req<any>("/api/pro/highlight/export", {
        method: "POST",
        body: JSON.stringify({ set_path, out_path, start_sec, duration_sec }),
      }),

    bpmRamp: (
      track_a_bpm: number,
      track_b_bpm: number,
      a_outro_start_sec: number,
      a_duration_sec: number,
      bars_per_step = 8,
    ) =>
      req<any>("/api/pro/bpmadjust/ramp", {
        method: "POST",
        body: JSON.stringify({
          track_a_bpm, track_b_bpm, a_outro_start_sec, a_duration_sec, bars_per_step,
        }),
      }),

    samplesScan: (folder: string) =>
      req<any>("/api/pro/samples/scan", { method: "POST", body: JSON.stringify({ folder }) }),
    samplesFind: (params: Record<string, any>) => {
      const qs = new URLSearchParams(
        Object.entries(params).filter(([, v]) => v != null && v !== "")
      ).toString();
      return req<{ samples: any[] }>(`/api/pro/samples/find?${qs}`);
    },

    masterBatch: (track_ids: number[], out_dir: string, target_lufs = -8) =>
      req<any>("/api/pro/mastering/batch", {
        method: "POST",
        body: JSON.stringify({ track_ids, out_dir, target_lufs }),
      }),

    venuesList: () => req<{ venues: any[] }>("/api/pro/venues"),
    venueSetlist: (venue_id: string, duration_minutes = 60) =>
      req<{ tracks: Track[] }>("/api/pro/venues/setlist", {
        method: "POST",
        body: JSON.stringify({ venue_id, duration_minutes }),
      }),

    styleAnalysis: (track_id: number) =>
      req<any>(`/api/pro/styleanalysis/${track_id}`),

    cloudExport: (out_path: string, include_covers = true) =>
      req<any>("/api/pro/cloud/export", {
        method: "POST",
        body: JSON.stringify({ out_path, include_covers }),
      }),
    cloudImport: (pack_path: string, merge = true) =>
      req<any>("/api/pro/cloud/import", {
        method: "POST",
        body: JSON.stringify({ pack_path, merge }),
      }),
    cloudDiff: (pack_path: string) =>
      req<any>("/api/pro/cloud/diff", {
        method: "POST",
        body: JSON.stringify({ pack_path, merge: false }),
      }),

    releasesSubscriptions: () => req<any>("/api/pro/releases/subscriptions"),
    releasesSubscribe: (name: string, kind = "artist", source = "beatport") =>
      req<any>("/api/pro/releases/subscribe", {
        method: "POST",
        body: JSON.stringify({ name, kind, source }),
      }),
    releasesUnsubscribe: (id: number) =>
      req<any>(`/api/pro/releases/subscribe/${id}`, { method: "DELETE" }),
    releasesAuto: () => req<any>("/api/pro/releases/auto", { method: "POST" }),
    releasesCheck: () => req<any>("/api/pro/releases/check", { method: "POST" }),
    releasesFeed: (unseen_only = true, limit = 100) =>
      req<{ releases: any[] }>(`/api/pro/releases/feed?unseen_only=${unseen_only}&limit=${limit}`),
  },

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
