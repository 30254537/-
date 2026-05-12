import { useEffect, useState } from "react";
import { Search, Filter } from "lucide-react";
import { useApp } from "../store";
import { TrackList } from "../components/TrackList";

export function Library() {
  const { tracks, loadTracks } = useApp();
  const [q, setQ] = useState("");
  const [genre, setGenre] = useState("");
  const [mood, setMood] = useState("");
  const [bpmMin, setBpmMin] = useState<string>("");
  const [bpmMax, setBpmMax] = useState<string>("");

  useEffect(() => {
    loadTracks();
  }, []);

  useEffect(() => {
    const t = setTimeout(() => {
      loadTracks({
        q: q || undefined,
        genre: genre || undefined,
        mood: mood || undefined,
        bpm_min: bpmMin ? Number(bpmMin) : undefined,
        bpm_max: bpmMax ? Number(bpmMax) : undefined,
      });
    }, 300);
    return () => clearTimeout(t);
  }, [q, genre, mood, bpmMin, bpmMax]);

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-4 grid-bg">
      <div className="flex items-center gap-3">
        <h2 className="font-display text-3xl font-bold tracking-wider text-white">
          <span className="text-neon-blue neon-text">LIBRARY</span>
        </h2>
        <span className="text-neutral-500 font-mono text-sm">({tracks.length})</span>
      </div>

      <div className="glass rounded-xl p-4 flex flex-wrap gap-3 items-center">
        <div className="flex items-center gap-2 flex-1 min-w-[200px]">
          <Search size={16} className="text-neon-pink" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search artist, title..."
            className="flex-1 bg-transparent border-none outline-none font-mono text-sm"
          />
        </div>
        <div className="flex items-center gap-1">
          <Filter size={14} className="text-neon-purple" />
          <select
            value={genre}
            onChange={(e) => setGenre(e.target.value)}
            className="bg-bg-1 border border-neon-purple/30 rounded px-2 py-1 font-mono text-xs"
          >
            <option value="">All Genres</option>
            {["House", "Tech House", "Deep House", "Techno", "Trance", "Drum & Bass", "Dubstep", "Hip-Hop"].map((g) => (
              <option key={g} value={g}>{g}</option>
            ))}
          </select>
          <select
            value={mood}
            onChange={(e) => setMood(e.target.value)}
            className="bg-bg-1 border border-neon-purple/30 rounded px-2 py-1 font-mono text-xs"
          >
            <option value="">All Moods</option>
            <option value="chill">Chill</option>
            <option value="warmup">Warmup</option>
            <option value="groove">Groove</option>
            <option value="peak">Peak</option>
            <option value="intense">Intense</option>
          </select>
          <input
            type="number"
            value={bpmMin}
            onChange={(e) => setBpmMin(e.target.value)}
            placeholder="BPM min"
            className="w-20 bg-bg-1 border border-neon-purple/30 rounded px-2 py-1 font-mono text-xs"
          />
          <input
            type="number"
            value={bpmMax}
            onChange={(e) => setBpmMax(e.target.value)}
            placeholder="BPM max"
            className="w-20 bg-bg-1 border border-neon-purple/30 rounded px-2 py-1 font-mono text-xs"
          />
        </div>
      </div>

      <TrackList tracks={tracks} />
    </div>
  );
}
