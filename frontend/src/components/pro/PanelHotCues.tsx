import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
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

      <motion.button
        whileHover={{ scale: 1.03 }}
        whileTap={{ scale: 0.97 }}
        onClick={generate}
        disabled={!track || loading}
        className="px-4 py-2 rounded-lg bg-gradient-to-r from-neon-pink to-neon-yellow text-black font-display font-bold tracking-wider flex items-center gap-2 disabled:opacity-40"
      >
        {loading ? <Loader2 size={14} className="animate-spin" /> : "🔥"}
        {t("pro.hotcues.generate")}
      </motion.button>

      {!track && (
        <p className="text-xs text-neutral-500 font-mono">{t("pro.hotcues.no_track")}</p>
      )}

      <AnimatePresence>
        {cues.length > 0 && (
          <motion.div
            key={track?.id}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-4"
          >
            {/* Waveform timeline with cue markers */}
            <div className="relative h-24 rounded-lg glass border border-neon-purple/20 overflow-hidden">
              <div className="absolute inset-0 grid-bg opacity-30" />
              {/* Track length axis */}
              <div className="absolute inset-x-0 top-1/2 h-px bg-gradient-to-r from-neon-blue/30 via-white/20 to-neon-pink/30" />

              {/* Faux waveform peaks */}
              <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none" viewBox="0 0 100 100">
                {Array.from({ length: 60 }, (_, i) => {
                  const h = 20 + Math.sin(i * 0.4) * 8 + Math.sin(i * 0.13) * 12 + Math.random() * 6;
                  return (
                    <rect
                      key={i}
                      x={i * 1.66}
                      y={50 - h / 2}
                      width={1.2}
                      height={h}
                      fill="url(#wf-grad)"
                      opacity={0.35}
                    />
                  );
                })}
                <defs>
                  <linearGradient id="wf-grad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#00e5ff" />
                    <stop offset="100%" stopColor="#ff2ea6" />
                  </linearGradient>
                </defs>
              </svg>

              {cues.map((c, i) => {
                const left = duration > 0 ? (c.time_sec / duration) * 100 : 0;
                const hex = `#${c.color.replace("0x", "").padStart(6, "0")}`;
                return (
                  <motion.div
                    key={c.slot}
                    initial={{ opacity: 0, scale: 0, y: 20 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    transition={{ delay: 0.08 * i, type: "spring", stiffness: 220, damping: 14 }}
                    className="absolute top-0 bottom-0 group"
                    style={{ left: `${left}%`, transform: "translateX(-50%)" }}
                    title={`${c.name} @ ${c.time_sec.toFixed(2)}s`}
                  >
                    <motion.div
                      animate={{
                        boxShadow: [
                          `0 0 6px ${hex}, 0 0 14px ${hex}40`,
                          `0 0 14px ${hex}, 0 0 28px ${hex}80`,
                          `0 0 6px ${hex}, 0 0 14px ${hex}40`,
                        ],
                      }}
                      transition={{ duration: 1.6, repeat: Infinity, delay: i * 0.1 }}
                      className="w-3.5 h-3.5 rounded-full mx-auto mt-3 border-2 border-bg-1"
                      style={{ background: hex }}
                    />
                    <div
                      className="w-px flex-1 mx-auto bg-gradient-to-b from-white/30 to-transparent"
                      style={{ height: 64 }}
                    />
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 text-[10px] font-mono font-bold text-white">
                      {c.slot + 1}
                    </div>
                  </motion.div>
                );
              })}
            </div>

            {/* Cue cards grid */}
            <motion.div
              variants={{
                visible: { transition: { staggerChildren: 0.06 } },
              }}
              initial="hidden"
              animate="visible"
              className="grid grid-cols-2 gap-2"
            >
              {cues.map((c) => {
                const hex = `#${c.color.replace("0x", "").padStart(6, "0")}`;
                return (
                  <motion.div
                    key={c.slot}
                    variants={{
                      hidden: { opacity: 0, x: -10 },
                      visible: { opacity: 1, x: 0 },
                    }}
                    whileHover={{ x: 4, transition: { duration: 0.15 } }}
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
                  </motion.div>
                );
              })}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
