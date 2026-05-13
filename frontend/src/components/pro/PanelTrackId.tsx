import { useState } from "react";
import { Loader2 } from "lucide-react";
import { useApp } from "../../store";
import { api, type Track, type TrackIdResult } from "../../api";
import { PanelTrackPicker } from "./PanelTrackPicker";

export function PanelTrackId() {
  const { t } = useApp();
  const [pickedTrack, setPickedTrack] = useState<Track | null>(null);
  const [path, setPath] = useState("");
  const [result, setResult] = useState<TrackIdResult | null>(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true);
    setResult(null);
    try {
      let r: TrackIdResult;
      if (pickedTrack) r = await api.pro.trackIdLibrary(pickedTrack.id);
      else if (path) r = await api.pro.trackIdFile(path);
      else return;
      setResult(r);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <PanelTrackPicker value={pickedTrack} onChange={setPickedTrack} />
      <div className="flex gap-3 items-center">
        <input
          value={path}
          onChange={(e) => setPath(e.target.value)}
          placeholder={t("pro.trackid.input")}
          className="flex-1 bg-bg-1 border border-neon-purple/30 rounded px-3 py-2 font-mono text-sm"
        />
        <button
          onClick={run}
          disabled={loading || (!pickedTrack && !path)}
          className="px-4 py-2 rounded-lg bg-gradient-to-r from-neon-pink to-neon-purple text-white font-display font-bold tracking-wider flex items-center gap-2 disabled:opacity-40"
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : "🎯"}
          {t("pro.trackid.id")}
        </button>
      </div>

      {!result && !loading && (
        <p className="text-xs text-neutral-500 font-mono">{t("pro.trackid.empty")}</p>
      )}

      {result && (
        <div className="space-y-3">
          <h4 className="font-display text-sm tracking-wider text-neon-blue">
            {t("pro.trackid.matches")}
          </h4>
          <div className="space-y-2">
            {result.local_matches.length === 0 && (
              <p className="text-xs text-neutral-500">No local match.</p>
            )}
            {result.local_matches.map((m, i) => (
              <div key={i} className="glass rounded-lg p-3 space-y-1">
                <div className="flex items-center justify-between">
                  <div className="font-mono text-sm">
                    <span className="text-neon-pink">{m.artist}</span> —{" "}
                    <span className="text-white">{m.title}</span>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-display font-black text-neon-green">
                      {(m.confidence * 100).toFixed(1)}%
                    </div>
                    <div className="text-[10px] font-mono text-neutral-500">
                      {t("pro.trackid.confidence")}
                    </div>
                  </div>
                </div>
                <div className="text-[11px] font-mono text-neutral-400">
                  {m.matched_landmarks} / {m.total_landmarks} {t("pro.trackid.matched")} ·{" "}
                  {m.metadata?.bpm} BPM · {m.metadata?.camelot}
                </div>
                <div className="h-1 rounded-full bg-bg-1 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-neon-pink to-neon-green"
                    style={{ width: `${m.confidence * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          {result.discogs && (
            <div className="glass rounded-lg p-3">
              <h5 className="text-xs font-mono text-neon-purple uppercase tracking-wider mb-2">
                {t("pro.trackid.discogs")}
              </h5>
              <div className="grid grid-cols-3 gap-2 text-xs font-mono">
                <div>
                  <div className="text-neutral-500">{t("pro.trackid.label")}</div>
                  <div className="text-neon-blue">{result.discogs.label ?? "-"}</div>
                </div>
                <div>
                  <div className="text-neutral-500">{t("pro.trackid.year")}</div>
                  <div className="text-neon-blue">{result.discogs.year ?? "-"}</div>
                </div>
                <div>
                  <div className="text-neutral-500">{t("pro.trackid.catno")}</div>
                  <div className="text-neon-blue">{result.discogs.catalog_number ?? "-"}</div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
