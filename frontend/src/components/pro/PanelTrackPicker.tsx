import { useEffect, useState } from "react";
import { useApp } from "../../store";
import { api, type Track } from "../../api";
import { Music2, Search } from "lucide-react";

/** Compact track picker — shows the currently selected pro-track and a search drawer. */
export function PanelTrackPicker({
  value,
  onChange,
}: {
  value: Track | null;
  onChange: (t: Track | null) => void;
}) {
  const { t } = useApp();
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [results, setResults] = useState<Track[]>([]);

  useEffect(() => {
    const id = setTimeout(async () => {
      const { tracks } = await api.listTracks({ q: q || undefined, limit: 50 });
      setResults(tracks);
    }, 250);
    return () => clearTimeout(id);
  }, [q]);

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-3">
        <button
          onClick={() => setOpen(!open)}
          className="px-3 py-2 rounded-lg bg-neon-blue/15 border border-neon-blue/40 text-neon-blue font-mono text-xs flex items-center gap-2"
        >
          <Music2 size={14} />
          {value ? `${value.artist ?? ""} — ${value.title ?? value.filename}` : t("common.no_track")}
        </button>
        {value && (
          <button
            onClick={() => onChange(null)}
            className="text-xs font-mono text-neutral-500 hover:text-neon-pink"
          >
            ✗
          </button>
        )}
      </div>

      {open && (
        <div className="glass rounded-xl p-4 space-y-3 max-h-[420px] overflow-y-auto">
          <div className="flex items-center gap-2 border-b border-neon-purple/30 pb-2">
            <Search size={16} className="text-neon-pink" />
            <input
              autoFocus
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder={t("library.search")}
              className="flex-1 bg-transparent outline-none font-mono text-sm"
            />
          </div>
          <div className="space-y-1">
            {results.map((track) => (
              <button
                key={track.id}
                onClick={() => {
                  onChange(track);
                  setOpen(false);
                }}
                className="w-full text-left p-2 rounded hover:bg-white/5 font-mono text-xs flex items-center gap-3"
              >
                <span className="text-neon-pink w-12">{track.bpm ?? "-"}</span>
                <span className="text-neon-blue w-10">{track.camelot ?? "-"}</span>
                <span className="text-neutral-300 truncate">
                  {track.artist} — {track.title ?? track.filename}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
