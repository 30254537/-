import { useEffect, useState } from "react";
import { Search, Filter } from "lucide-react";
import { useApp } from "../store";
import { TrackList } from "../components/TrackList";

export function Library() {
  const { tracks, loadTracks, t } = useApp();
  const [q, setQ] = useState("");
  const [genre, setGenre] = useState("");
  const [mood, setMood] = useState("");
  const [bpmMin, setBpmMin] = useState<string>("");
  const [bpmMax, setBpmMax] = useState<string>("");
  const [vocalGender, setVocalGender] = useState<string>("");

  useEffect(() => {
    loadTracks();
  }, []);

  useEffect(() => {
    const id = setTimeout(() => {
      // The gender filter is client-side because the existing /api/tracks
      // endpoint doesn't accept a vocal_gender param yet.
      loadTracks({
        q: q || undefined,
        genre: genre || undefined,
        mood: mood || undefined,
        bpm_min: bpmMin ? Number(bpmMin) : undefined,
        bpm_max: bpmMax ? Number(bpmMax) : undefined,
      });
    }, 300);
    return () => clearTimeout(id);
  }, [q, genre, mood, bpmMin, bpmMax]);

  // Apply gender filter on already-loaded tracks
  const visibleTracks = vocalGender
    ? tracks.filter((tr) => (tr.vocal_gender ?? "none") === vocalGender)
    : tracks;

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-4 grid-bg">
      <div className="flex items-center gap-3">
        <h2 className="font-display text-3xl font-bold tracking-wider text-white">
          <span className="text-neon-blue neon-text">{t("library.title")}</span>
        </h2>
        <span className="text-neutral-500 font-mono text-sm">({tracks.length})</span>
      </div>

      <div className="glass rounded-xl p-4 flex flex-wrap gap-3 items-center">
        <div className="flex items-center gap-2 flex-1 min-w-[200px]">
          <Search size={16} className="text-neon-pink" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder={t("library.search")}
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
            <option value="">{t("library.all_genres")}</option>
            {["House", "Tech House", "Deep House", "Techno", "Trance", "Drum & Bass", "Dubstep", "Hip-Hop"].map((g) => (
              <option key={g} value={g}>{g}</option>
            ))}
          </select>
          <select
            value={mood}
            onChange={(e) => setMood(e.target.value)}
            className="bg-bg-1 border border-neon-purple/30 rounded px-2 py-1 font-mono text-xs"
          >
            <option value="">{t("library.all_moods")}</option>
            <option value="chill">{t("mood.chill")}</option>
            <option value="warmup">{t("mood.warmup")}</option>
            <option value="groove">{t("mood.groove")}</option>
            <option value="peak">{t("mood.peak")}</option>
            <option value="intense">{t("mood.intense")}</option>
          </select>
          <input
            type="number"
            value={bpmMin}
            onChange={(e) => setBpmMin(e.target.value)}
            placeholder={t("library.bpm_min")}
            className="w-24 bg-bg-1 border border-neon-purple/30 rounded px-2 py-1 font-mono text-xs"
          />
          <input
            type="number"
            value={bpmMax}
            onChange={(e) => setBpmMax(e.target.value)}
            placeholder={t("library.bpm_max")}
            className="w-24 bg-bg-1 border border-neon-purple/30 rounded px-2 py-1 font-mono text-xs"
          />
          <select
            value={vocalGender}
            onChange={(e) => setVocalGender(e.target.value)}
            className="bg-bg-1 border border-neon-purple/30 rounded px-2 py-1 font-mono text-xs"
          >
            <option value="">{t("library.all_vocals")}</option>
            <option value="male">{t("vocal.male")}</option>
            <option value="female">{t("vocal.female")}</option>
            <option value="mixed">{t("vocal.mixed")}</option>
            <option value="none">{t("vocal.none")}</option>
          </select>
        </div>
      </div>

      <TrackList tracks={visibleTracks} />
    </div>
  );
}
