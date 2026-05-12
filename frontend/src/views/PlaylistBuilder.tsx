import { useState } from "react";
import { Wand2, Download, Save } from "lucide-react";
import { api, type Track } from "../api";
import { TrackList } from "../components/TrackList";

const CURVES = [
  { id: "warmup", label: "Warmup", desc: "Ease in — low to mid energy (3 → 6)" },
  { id: "peak-time", label: "Peak Time", desc: "Classic arc, big energy at center" },
  { id: "after-hours", label: "After Hours", desc: "Wind-down — high to low (5 → 2)" },
  { id: "festival", label: "Festival", desc: "Relentless ramp to full energy" },
  { id: "journey", label: "DJ Journey", desc: "3-act — warmup, peak, cooldown" },
];

export function PlaylistBuilder() {
  const [duration, setDuration] = useState(60);
  const [curve, setCurve] = useState("journey");
  const [genre, setGenre] = useState("");
  const [bpmMin, setBpmMin] = useState("");
  const [bpmMax, setBpmMax] = useState("");
  const [saveAs, setSaveAs] = useState("");
  const [tracks, setTracks] = useState<Track[]>([]);
  const [loading, setLoading] = useState(false);

  const generate = async () => {
    setLoading(true);
    try {
      const r = await api.generatePlaylist({
        duration_minutes: duration,
        curve,
        genre: genre || undefined,
        bpm_min: bpmMin ? Number(bpmMin) : undefined,
        bpm_max: bpmMax ? Number(bpmMax) : undefined,
        save_as: saveAs || undefined,
      });
      setTracks(r.tracks);
    } finally {
      setLoading(false);
    }
  };

  const exportM3u = () => {
    const lines = ["#EXTM3U"];
    tracks.forEach((t) => {
      lines.push(`#EXTINF:${Math.round(t.duration ?? 0)},${t.artist ?? ""} - ${t.title ?? ""}`);
      lines.push(t.path);
    });
    const blob = new Blob([lines.join("\n")], { type: "audio/x-mpegurl" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${saveAs || "mixmind"}.m3u8`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-4 grid-bg">
      <h2 className="font-display text-3xl font-bold tracking-wider">
        <span className="text-neon-purple neon-text">PLAYLIST</span>{" "}
        <span className="text-neon-pink neon-text">BUILDER</span>
      </h2>

      <div className="glass rounded-xl p-6 space-y-4 neon-border">
        <div className="grid grid-cols-5 gap-3">
          {CURVES.map((c) => (
            <button
              key={c.id}
              onClick={() => setCurve(c.id)}
              className={`p-3 rounded-lg border text-left transition ${
                curve === c.id
                  ? "bg-neon-pink/10 border-neon-pink text-white shadow-[0_0_20px_rgba(255,46,166,0.3)]"
                  : "border-white/10 text-neutral-400 hover:border-neon-purple/50"
              }`}
            >
              <div className="font-display font-bold text-sm">{c.label}</div>
              <div className="text-[10px] font-mono mt-1 opacity-70">{c.desc}</div>
            </button>
          ))}
        </div>

        <div className="grid grid-cols-6 gap-3 items-end">
          <Field label="Duration (min)">
            <input
              type="number"
              value={duration}
              onChange={(e) => setDuration(+e.target.value)}
              className="bg-bg-1 border border-neon-purple/30 rounded px-3 py-2 font-mono text-sm w-full"
            />
          </Field>
          <Field label="Genre">
            <select
              value={genre}
              onChange={(e) => setGenre(e.target.value)}
              className="bg-bg-1 border border-neon-purple/30 rounded px-3 py-2 font-mono text-sm w-full"
            >
              <option value="">Any</option>
              {["House", "Tech House", "Deep House", "Techno", "Trance", "Drum & Bass", "Dubstep", "Hip-Hop"].map((g) => (
                <option key={g} value={g}>{g}</option>
              ))}
            </select>
          </Field>
          <Field label="BPM min">
            <input
              type="number"
              value={bpmMin}
              onChange={(e) => setBpmMin(e.target.value)}
              className="bg-bg-1 border border-neon-purple/30 rounded px-3 py-2 font-mono text-sm w-full"
            />
          </Field>
          <Field label="BPM max">
            <input
              type="number"
              value={bpmMax}
              onChange={(e) => setBpmMax(e.target.value)}
              className="bg-bg-1 border border-neon-purple/30 rounded px-3 py-2 font-mono text-sm w-full"
            />
          </Field>
          <Field label="Save as">
            <input
              value={saveAs}
              onChange={(e) => setSaveAs(e.target.value)}
              placeholder="Club Night — Fri"
              className="bg-bg-1 border border-neon-purple/30 rounded px-3 py-2 font-mono text-sm w-full"
            />
          </Field>
          <button
            onClick={generate}
            disabled={loading}
            className="px-4 py-2 rounded-lg bg-gradient-to-r from-neon-pink to-neon-purple text-white font-display font-bold tracking-wider flex items-center justify-center gap-2 hover:shadow-[0_0_20px_rgba(255,46,166,0.5)] transition disabled:opacity-40"
          >
            <Wand2 size={16} className={loading ? "animate-spin" : ""} />
            GENERATE
          </button>
        </div>
      </div>

      {tracks.length > 0 && (
        <>
          <div className="flex items-center justify-between">
            <p className="font-mono text-sm text-neutral-400">
              {tracks.length} tracks —{" "}
              {Math.round(tracks.reduce((s, t) => s + (t.duration ?? 0), 0) / 60)} min
            </p>
            <div className="flex gap-2">
              <button
                onClick={exportM3u}
                className="px-3 py-1.5 rounded bg-neon-blue/20 border border-neon-blue/40 text-neon-blue font-mono text-xs flex items-center gap-2"
              >
                <Download size={14} />
                EXPORT .M3U8
              </button>
            </div>
          </div>
          <TrackList tracks={tracks} />
        </>
      )}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs font-mono text-neon-purple uppercase tracking-wider mb-1">
        {label}
      </label>
      {children}
    </div>
  );
}
