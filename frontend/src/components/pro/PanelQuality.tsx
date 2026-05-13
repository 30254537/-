import { useState } from "react";
import { Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useApp } from "../../store";
import { api, type Track, type QualityReport } from "../../api";
import { PanelTrackPicker } from "./PanelTrackPicker";
import { CountUp } from "../CountUp";

const VERDICT_COLORS: Record<string, string> = {
  pristine:   "from-neon-green/40 to-neon-green/10 text-neon-green border-neon-green/40",
  lossless:   "from-neon-green/40 to-neon-green/10 text-neon-green border-neon-green/40",
  lossy_320:  "from-neon-blue/40 to-neon-blue/10 text-neon-blue border-neon-blue/40",
  lossy:      "from-neon-yellow/40 to-neon-yellow/10 text-neon-yellow border-neon-yellow/40",
  fake_320:   "from-red-500/40 to-red-500/10 text-red-400 border-red-500/40",
  very_lossy: "from-red-500/40 to-red-500/10 text-red-400 border-red-500/40",
  error:      "from-neutral-700/40 to-neutral-700/10 text-neutral-300 border-neutral-700",
};

export function PanelQuality() {
  const { t } = useApp();
  const [track, setTrack] = useState<Track | null>(null);
  const [report, setReport] = useState<QualityReport | null>(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    if (!track) return;
    setLoading(true);
    setReport(null);
    try {
      const r = await api.pro.qualityTrack(track.id);
      setReport(r);
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
        onClick={run}
        disabled={!track || loading}
        className="px-4 py-2 rounded-lg bg-gradient-to-r from-neon-yellow to-neon-pink text-black font-display font-bold tracking-wider flex items-center gap-2 disabled:opacity-40"
      >
        {loading ? <Loader2 size={14} className="animate-spin" /> : "🎵"}
        {t("pro.quality.run")}
      </motion.button>

      <AnimatePresence mode="wait">
        {report && (
          <motion.div
            key={track?.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="space-y-3"
          >
            {/* Verdict pill */}
            <motion.div
              initial={{ scale: 0.94 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", stiffness: 200 }}
              className={`rounded-xl p-4 border bg-gradient-to-r ${
                VERDICT_COLORS[report.verdict] ?? VERDICT_COLORS.error
              }`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-[10px] uppercase font-mono opacity-70 tracking-widest">
                    {t("pro.quality.verdict")}
                  </div>
                  <div className="font-display text-2xl font-black tracking-wider">
                    {t(`verdict.${report.verdict}`)}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] uppercase font-mono opacity-70">
                    {t("pro.quality.score")}
                  </div>
                  <div className="font-display text-3xl font-black">
                    <CountUp value={report.score * 100} duration={900} decimals={0} />
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-3 mt-3 text-[11px] font-mono">
                <div>
                  <span className="opacity-70">{t("pro.quality.declared")}: </span>
                  <span className="font-bold">{report.declared_bitrate_kbps ?? "?"} kbps</span>
                </div>
                <div>
                  <span className="opacity-70">{t("pro.quality.cutoff")}: </span>
                  <span className="font-bold">
                    {(report.measured_cutoff_hz / 1000).toFixed(1)} kHz
                  </span>
                </div>
                <div>
                  <span className="opacity-70">SR: </span>
                  <span className="font-bold">{report.sample_rate} Hz</span>
                </div>
              </div>
              {report.notes?.length > 0 && (
                <ul className="mt-2 list-disc list-inside text-[10px] font-mono opacity-90 space-y-0.5">
                  {report.notes.map((n, i) => (
                    <motion.li
                      key={i}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.2 + i * 0.05 }}
                    >
                      {n}
                    </motion.li>
                  ))}
                </ul>
              )}
            </motion.div>

            {/* Spectrum visualization — staggered bar entry */}
            <div className="glass rounded-lg p-3 space-y-1">
              <div className="text-[10px] uppercase font-mono text-neon-purple tracking-widest">
                Frequency spectrum (dB) — cutoff visible as a brick wall
              </div>
              <svg
                viewBox={`0 0 ${report.spectrum_db.length} 100`}
                className="w-full h-32"
                preserveAspectRatio="none"
              >
                {report.spectrum_db.map((db, i) => {
                  const h = Math.max(0, 100 + db);
                  const isAboveCutoff =
                    (i / report.spectrum_db.length) * (report.sample_rate / 2) >
                    report.measured_cutoff_hz;
                  return (
                    <motion.rect
                      key={i}
                      initial={{ height: 0, y: 100 }}
                      animate={{ height: h, y: 100 - h }}
                      transition={{
                        duration: 0.5,
                        delay: (i / report.spectrum_db.length) * 0.6,
                        ease: "easeOut",
                      }}
                      x={i}
                      width={1}
                      fill={isAboveCutoff ? "#ff2ea6" : "#00e5ff"}
                      opacity={isAboveCutoff ? 0.45 : 0.9}
                    />
                  );
                })}
                {/* Cutoff dashed line drawn after bars */}
                <motion.line
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.8 }}
                  x1={
                    (report.measured_cutoff_hz / (report.sample_rate / 2)) *
                    report.spectrum_db.length
                  }
                  x2={
                    (report.measured_cutoff_hz / (report.sample_rate / 2)) *
                    report.spectrum_db.length
                  }
                  y1={0}
                  y2={100}
                  stroke="#fff02e"
                  strokeWidth={0.8}
                  strokeDasharray="3 2"
                />
                {/* Cutoff label */}
                <motion.text
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 1 }}
                  x={
                    (report.measured_cutoff_hz / (report.sample_rate / 2)) *
                      report.spectrum_db.length +
                    2
                  }
                  y={8}
                  fontSize={4}
                  fill="#fff02e"
                  fontFamily="JetBrains Mono, monospace"
                >
                  {(report.measured_cutoff_hz / 1000).toFixed(1)}kHz
                </motion.text>
              </svg>
              <div className="flex justify-between text-[9px] font-mono text-neutral-500">
                <span>0 Hz</span>
                <span>{(report.sample_rate / 2 / 1000).toFixed(1)} kHz</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
