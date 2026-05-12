import { create } from "zustand";
import { api, Track, Stats } from "./api";

type View = "dashboard" | "library" | "recommend" | "playlist" | "dedupe";

interface AppState {
  view: View;
  setView: (v: View) => void;

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

export const useApp = create<AppState>((set, get) => ({
  view: "dashboard",
  setView: (v) => set({ view: v }),

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
    // Update in list
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
