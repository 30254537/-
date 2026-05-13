import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { useApp } from "../../store";
import { api, type Track, type PhraseGrid } from "../../api";
import { PanelTrackPicker } from "./PanelTrackPicker";

const SECTION_COLORS: Record<string, string> = {
  intro:      "from-neon-blue/30 to-neon-blue/10 border-neon-blue/40",
  main:       "from-neutral-700/50 to-neutral-800/40 border-neutral-600/40",
  drop:       "from-neon-pink/40 to-neon-pink/10 border-neon-pink/50",
  breakdown:  "from-neon-purple/30 to-neon-purple/10 border-neon-purple/40",
  outro:      "from-neon-yellow/25 to-neon-yellow/5 border-neon-yellow/40",
  outro_lead: "from-neon-yellow/15 to-neon-yellow/5 border-neon-yellow/30",
};

export function PanelPhraseGrid() {
  const { t } = useApp();
  const [track, setTrack] = useState<Track | null>(null);
  const [grid, setGrid] = useState<PhraseGrid | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!track) {
      setGrid(null);
      return;
    }
    setLoading(true);
    api.pro
      .phraseGrid(track.id, 32)
      .then(setGrid)
      .catch(() => setGrid(null))
      .finally(() => setLoading(false));
  }, [track?.id]);

  const totalDur = grid?.sections?.[grid.sections.length - 1]?.end_sec ?? 1;

  return (
    <div className="space-y-4">
      <PanelTrackPicker value={track} onChange={setTrack} />

      {loading && (
        <div className="flex items-center gap-2 text-xs text-neon-blue font-mono">
          <Loader2 size={14} className="animate-spin" />
          {t("common.loading")}
        </div>
      )}

      {grid && (
        <div className="space-y-4">
          <div className="flex items-center gap-3 text-xs font-mono text-neutral-400">
            <span>
              <span className="text-neon-blue">{grid.bpm}</span> BPM
            </span>
            <span>·</span>
            <span>
              <span className="text-neon-pink">{grid.total_bars}</span> {t("pro.phrasegrid.bars")}
            </span>
            <span>·</span>
            <span>{grid.bars_per_phrase}-bar phrases</span>
          </div>

          {/* Section ribbon — colour-coded sections */}
          <div className="flex h-14 rounded-lg overflow-hidden border border-white/10">
            {grid.sections.map((s, i) => {
              const w = ((s.end_sec - s.start_sec) / totalDur) * 100;
              const colors = SECTION_COLORS[s.label] ?? SECTION_COLORS.main;
              return (
                <div
                  key={i}
                  className={`relative bg-gradient-to-b ${colors} border-r border-white/5 flex items-center justify-center text-[10px] font-mono uppercase tracking-wider`}
                  style={{ width: `${w}%` }}
                  title={`${s.start_sec.toFixed(1)}–${s.end_sec.toFixed(1)}s`}
                >
                  <span className="opacity-90">
                    {t(`pro.phrasegrid.section.${s.label}`)}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Phrase boundary tickmarks */}
          <div className="relative h-8 rounded bg-bg-1 border border-neon-purple/20">
            {grid.boundaries.map((b, i) => {
              const left = (b.time_sec / totalDur) * 100;
              const isPhrase = b.type === "32";
              return (
                <div
                  key={i}
                  className={`absolute top-0 bottom-0 ${
                    isPhrase
                      ? "border-l-2 border-neon-pink"
                      : b.type === "16"
                      ? "border-l border-neon-purple"
                      : "border-l border-neon-blue/40"
                  }`}
                  style={{ left: `${left}%` }}
                  title={`Bar ${b.bar} (${b.time_sec.toFixed(2)}s)`}
                >
                  {isPhrase && (
                    <span className="absolute -top-4 -translate-x-1/2 text-[9px] font-mono text-neon-pink">
                      {b.bar}
                    </span>
                  )}
                </div>
              );
            })}
          </div>

          {/* Mix in / out points */}
          <div className="grid grid-cols-2 gap-3">
            <div className="glass rounded-lg p-3">
              <div className="text-[10px] font-mono uppercase text-neon-green mb-2">
                {t("pro.phrasegrid.mix_in_points")}
              </div>
              <div className="space-y-1">
                {grid.mix_in_points.map((p, i) => (
                  <div key={i} className="text-xs font-mono text-white">
                    {p.toFixed(2)}s
                  </div>
                ))}
                {grid.mix_in_points.length === 0 && <div className="text-xs text-neutral-500">-</div>}
              </div>
            </div>
            <div className="glass rounded-lg p-3">
              <div className="text-[10px] font-mono uppercase text-neon-yellow mb-2">
                {t("pro.phrasegrid.mix_out_points")}
              </div>
              <div className="space-y-1">
                {grid.mix_out_points.map((p, i) => (
                  <div key={i} className="text-xs font-mono text-white">
                    {p.toFixed(2)}s
                  </div>
                ))}
                {grid.mix_out_points.length === 0 && <div className="text-xs text-neutral-500">-</div>}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
