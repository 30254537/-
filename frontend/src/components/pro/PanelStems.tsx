import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { useApp } from "../../store";
import { api, type Track } from "../../api";
import { PanelTrackPicker } from "./PanelTrackPicker";

export function PanelStems() {
  const { t } = useApp();
  const [track, setTrack] = useState<Track | null>(null);
  const [caps, setCaps] = useState<{ available: boolean; backend: string | null; install_hint: string | null } | null>(null);
  const [stems, setStems] = useState<Record<string, string> | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.pro.stemsCapabilities().then(setCaps).catch(() => {});
  }, []);

  const run = async () => {
    if (!track) return;
    setLoading(true);
    setStems(null);
    try {
      const r = await api.pro.stemsSeparate(track.id);
      setStems(r.stems);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <PanelTrackPicker value={track} onChange={setTrack} />

      {caps && !caps.available && (
        <div className="glass rounded-lg p-3 border border-neon-yellow/40 text-xs font-mono text-neon-yellow">
          ⚠ {t("pro.stems.unavailable")}
          <div className="mt-1 text-[10px] text-neutral-400">
            {caps.install_hint ?? t("pro.stems.install")}
          </div>
        </div>
      )}

      <button
        onClick={run}
        disabled={!track || loading || (caps !== null && !caps.available)}
        className="px-4 py-2 rounded-lg bg-gradient-to-r from-neon-blue to-neon-purple text-white font-display font-bold tracking-wider flex items-center gap-2 disabled:opacity-40"
      >
        {loading ? <Loader2 size={14} className="animate-spin" /> : "💎"}
        {t("pro.stems.run")}
      </button>

      {stems && (
        <div className="space-y-2">
          {(["vocals", "drums", "bass", "other"] as const).map((s) => {
            const colors: Record<string, string> = {
              vocals: "from-neon-pink/40 to-neon-pink/10 text-neon-pink border-neon-pink/40",
              drums:  "from-neon-yellow/40 to-neon-yellow/10 text-neon-yellow border-neon-yellow/40",
              bass:   "from-neon-purple/40 to-neon-purple/10 text-neon-purple border-neon-purple/40",
              other:  "from-neon-blue/40 to-neon-blue/10 text-neon-blue border-neon-blue/40",
            };
            return (
              <div
                key={s}
                className={`glass rounded-lg p-3 border bg-gradient-to-r ${colors[s]}`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-display font-bold tracking-wider text-sm">
                    {t(`pro.stems.${s}`)}
                  </span>
                  <span className="font-mono text-[10px] text-neutral-300 truncate ml-2">
                    {stems[s]?.split("/").pop() ?? "-"}
                  </span>
                </div>
                <div className="mt-2 h-2 rounded-full bg-bg-1 overflow-hidden">
                  <div
                    className={`h-full bg-current opacity-60`}
                    style={{ width: stems[s] ? "100%" : "0%" }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
