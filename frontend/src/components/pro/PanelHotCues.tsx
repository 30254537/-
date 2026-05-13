import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { useApp } from "../../store";
import { api, type Track, type HotCue } from "../../api";
import { PanelTrackPicker } from "./PanelTrackPicker";

export function PanelHotCues() {
  const { t } = useApp();
  const [track, setTrack] = useState<Track | null>(null);
  const [cues, setCues] = useState<HotCue[]>([]);
  const [duration, setDuration] = useState<number>(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!track) {
      setCues([]);
      return;
    }
    api.pro.hotCuesGet(track.id).then((r) => {
      setCues(r.cues || []);
      setDuration(track.duration ?? 0);
    });
  }, [track?.id]);

  const generate = async () => {
    if (!track) return;
    setLoading(true);
    try {
      const r = await api.pro.hotCuesGenerate(track.id, true);
      setCues(r.cues);
      setDuration(r.duration || track.duration || 0);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <PanelTrackPicker value={track} onChange={setTrack} />

      <button
        onClick={generate}
        disabled={!track || loading}
        className="px-4 py-2 rounded-lg bg-gradient-to-r from-neon-pink to-neon-yellow text-black font-display font-bold tracking-wider flex items-center gap-2 disabled:opacity-40"
      >
        {loading ? <Loader2 size={14} className="animate-spin" /> : "🔥"}
        {t("pro.hotcues.generate")}
      </button>

      {!track && (
        <p className="text-xs text-neutral-500 font-mono">{t("pro.hotcues.no_track")}</p>
      )}

      {cues.length > 0 && (
        <>
          {/* Waveform timeline with cue markers */}
          <div className="relative h-20 rounded-lg glass border border-neon-purple/20 overflow-hidden">
            <div className="absolute inset-0 grid-bg opacity-30" />
            {/* Track length axis */}
            <div className="absolute inset-x-0 top-1/2 h-px bg-gradient-to-r from-neon-blue/30 via-white/20 to-neon-pink/30" />

            {cues.map((c) => {
              const left = duration > 0 ? (c.time_sec / duration) * 100 : 0;
              return (
                <div
                  key={c.slot}
                  className="absolute top-0 bottom-0 group"
                  style={{ left: `${left}%`, transform: "translateX(-50%)" }}
                  title={`${c.name} @ ${c.time_sec.toFixed(2)}s`}
                >
                  <div
                    className="w-3 h-3 rounded-full mx-auto mt-2 border-2 border-bg-1"
                    style={{
                      background: `#${c.color.replace("0x", "").padStart(6, "0")}`,
                      boxShadow: `0 0 12px #${c.color.replace("0x", "").padStart(6, "0")}`,
                    }}
                  />
                  <div className="w-px flex-1 mx-auto bg-gradient-to-b from-white/30 to-transparent" style={{ height: 64 }} />
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 text-[9px] font-mono font-bold text-white">
                    {c.slot + 1}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Cue cards grid */}
          <div className="grid grid-cols-2 gap-2">
            {cues.map((c) => {
              const hex = `#${c.color.replace("0x", "").padStart(6, "0")}`;
              return (
                <div
                  key={c.slot}
                  className="glass rounded-lg p-2 flex items-center gap-3"
                  style={{ borderLeft: `3px solid ${hex}` }}
                >
                  <div
                    className="w-7 h-7 rounded font-display font-black text-sm flex items-center justify-center text-bg-1"
                    style={{ background: hex }}
                  >
                    {c.slot + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-mono text-xs text-white truncate">
                      {t(`cue.${c.type}`)}
                    </div>
                    <div className="font-mono text-[10px] text-neutral-400">
                      {Math.floor(c.time_sec / 60)}:
                      {String(Math.floor(c.time_sec % 60)).padStart(2, "0")}
                      .{String(Math.floor((c.time_sec * 100) % 100)).padStart(2, "0")}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
