import { create } from "zustand";
import { api, Track, Stats } from "./api";
import { translate, type Lang } from "./i18n";

type View = "dashboard" | "library" | "recommend" | "playlist" | "dedupe" | "pro" | "proplus";

interface AppState {
  view: View;
  setView: (v: View) => void;

  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: string) => string;

  stats: Stats | null;
  loadStats: () => Promise<void>;

  tracks: Track[];
  loadTracks: (params?: Record<string, any>) => Promise<void>;

  currentTrack: Track | null;
  setCurrentTrack: (t: Track | null) => void;

  isPlaying: boolean;
  setIsPlaying: (p: boolean) => void;

  rate: (id: number, rating: number) => Promise<void>;
}

const STORAGE_KEY = "mixmind.lang";
const initialLang: Lang =
  (typeof localStorage !== "undefined" &&
    (localStorage.getItem(STORAGE_KEY) as Lang)) ||
  (typeof navigator !== "undefined" && navigator.language?.startsWith("zh")
    ? "zh"
    : "en");

export const useApp = create<AppState>((set, get) => ({
  view: "dashboard",
  setView: (v) => set({ view: v }),

  lang: initialLang,
  setLang: (l) => {
    try {
      localStorage.setItem(STORAGE_KEY, l);
    } catch {}
    set({ lang: l });
  },
  t: (key) => translate(key, get().lang),

  stats: null,
  loadStats: async () => {
    try {
      const s = await api.stats();
      set({ stats: s });
    } catch (e) {
      console.error(e);
    }
  },

  tracks: [],
  loadTracks: async (params = {}) => {
    const { tracks } = await api.listTracks({ limit: 200, ...params });
    set({ tracks });
  },

  currentTrack: null,
  setCurrentTrack: (t) => set({ currentTrack: t }),

  isPlaying: false,
  setIsPlaying: (p) => set({ isPlaying: p }),

  rate: async (id, rating) => {
    await api.rateTrack(id, rating);
    set((s) => ({
      tracks: s.tracks.map((t) => (t.id === id ? { ...t, rating } : t)),
      currentTrack:
        s.currentTrack && s.currentTrack.id === id
          ? { ...s.currentTrack, rating }
          : s.currentTrack,
    }));
    get().loadStats();
  },
}));
