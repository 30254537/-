import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useApp } from "../../store";
import { api, type Track, type MixCandidate } from "../../api";
import { PanelTrackPicker } from "./PanelTrackPicker";
import { CountUp } from "../CountUp";

const MODES = [
  { id: "steady",  key: "pro.livemix.steady" },
  { id: "build",   key: "pro.livemix.build" },
  { id: "release", key: "pro.livemix.release" },
];

export function PanelLiveMix() {
  const { t, setCurrentTrack, setIsPlaying } = useApp();
  const [deckA, setDeckA] = useState<Track | null>(null);
  const [mode, setMode] = useState("steady");
  const [candidates, setCandidates] = useState<MixCandidate[]>([]);
  const [loading, setLoading] = useState(false);

  const refresh = async () => {
    if (!deckA) return;
    setLoading(true);
    try {
      const r = await api.pro.liveMixSuggest(deckA.id, mode, 3);
      setCandidates(r.candidates);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (deckA) refresh();
  }, [deckA?.id, mode]);

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <div className="text-xs font-mono text-neon-purple uppercase tracking-wider">
          {t("pro.livemix.deck_a")}
        </div>
        <PanelTrackPicker value={deckA} onChange={setDeckA} />
      </div>

      <div className="flex items-center gap-2">
        <span className="text-xs font-mono text-neon-purple uppercase tracking-wider mr-2">
          {t("pro.livemix.mode")}:
        </span>
        {MODES.map((m) => (
          <motion.button
            key={m.id}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setMode(m.id)}
            className={`px-3 py-1 rounded font-mono text-xs transition-colors ${
              mode === m.id
                ? "bg-neon-pink text-white shadow-[0_0_15px_rgba(255,46,166,0.4)]"
                : "bg-bg-1 text-neutral-400 border border-neon-purple/30 hover:text-white"
            }`}
          >
            {t(m.key)}
          </motion.button>
        ))}
      </div>

      {!deckA && (
        <p className="text-xs text-neutral-500 font-mono">{t("pro.livemix.no_track")}</p>
      )}

      {loading && (
        <div className="flex items-center gap-2 text-xs text-neon-pink font-mono">
          <Loader2 size={14} className="animate-spin" />
          {t("common.thinking")}
        </div>
      )}

      <AnimatePresence mode="wait">
        {candidates.length > 0 && !loading && (
          <motion.div
            key={`${deckA?.id}-${mode}`}
            initial="hidden"
            animate="visible"
            exit={{ opacity: 0 }}
            variants={{
              hidden: { opacity: 0 },
              visible: { opacity: 1, transition: { staggerChildren: 0.12 } },
            }}
            className="space-y-2"
          >
            <div className="text-xs font-mono text-neon-purple uppercase tracking-wider">
              {t("pro.livemix.deck_b")}
            </div>
            {candidates.map((c, i) => (
              <motion.div
                key={c.track.id}
                variants={{
                  hidden: { opacity: 0, x: 20, scale: 0.95 },
                  visible: { opacity: 1, x: 0, scale: 1 },
                }}
                whileHover={{ scale: 1.01, borderColor: "rgba(255,46,166,0.6)" }}
                className="glass rounded-lg p-3 space-y-2 border border-neon-pink/20"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="font-mono text-sm truncate">
                      <span className="text-neon-pink">{c.track.artist}</span> —{" "}
                      <span className="text-white">{c.track.title ?? c.track.filename}</span>
                    </div>
                    <div className="text-[11px] font-mono text-neutral-400 mt-1">
                      {c.track.bpm} BPM · {c.track.camelot} · E{c.track.energy}
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="text-2xl font-display font-black text-neon-green">
                      <CountUp value={c.mix_score * 100} duration={900} decimals={0} />
                    </div>
                    <div className="text-[10px] font-mono text-neutral-500 uppercase tracking-wider">
                      {t("pro.livemix.score")}
                    </div>
                  </div>
                </div>

                {/* Score progress bar */}
                <motion.div
                  className="h-1 rounded-full bg-bg-1 overflow-hidden"
                >
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${c.mix_score * 100}%` }}
                    transition={{ duration: 1, delay: 0.2 + i * 0.1, ease: "easeOut" }}
                    className="h-full bg-gradient-to-r from-neon-blue via-neon-purple to-neon-pink"
                  />
                </motion.div>

                <div className="flex flex-wrap gap-1">
                  {c.reasons.map((r, ri) => (
                    <motion.span
                      key={r}
                      initial={{ opacity: 0, scale: 0.7 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 0.3 + ri * 0.05 + i * 0.1 }}
                      className="px-2 py-0.5 rounded-full bg-neon-blue/15 border border-neon-blue/40 text-neon-blue text-[10px] font-mono"
                    >
                      {t(`reason.${r}`)}
                    </motion.span>
                  ))}
                </div>

                <div className="grid grid-cols-3 gap-2 text-[11px] font-mono">
                  <div>
                    <span className="text-neutral-500">{t("pro.livemix.bpm_drift")}: </span>
                    <span className={c.bpm_pct_change < 0 ? "text-neon-blue" : "text-neon-pink"}>
                      {c.bpm_pct_change > 0 ? "+" : ""}
                      {c.bpm_pct_change.toFixed(2)}%
                    </span>
                  </div>
                  {c.mix_in_at !== null && (
                    <div>
                      <span className="text-neutral-500">{t("pro.livemix.mix_in")} </span>
                      <span className="text-neon-yellow">{c.mix_in_at.toFixed(1)}s</span>
                    </div>
                  )}
                  {c.mix_out_at !== null && (
                    <div>
                      <span className="text-neutral-500">{t("pro.livemix.mix_out")} </span>
                      <span className="text-neon-yellow">{c.mix_out_at.toFixed(1)}s</span>
                    </div>
                  )}
                </div>

                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => {
                    setCurrentTrack(c.track);
                    setIsPlaying(true);
                    api.pro.liveMixPlayed(c.track.id).catch(() => {});
                    setDeckA(c.track);
                  }}
                  className="w-full mt-1 py-1.5 rounded bg-gradient-to-r from-neon-pink to-neon-purple text-white text-xs font-display font-bold tracking-wider hover:shadow-[0_0_15px_rgba(255,46,166,0.5)] transition"
                >
                  {t("pro.livemix.cue")} #{i + 1}
                </motion.button>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
